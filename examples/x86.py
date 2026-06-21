import argparse

import libcfg
from libcfg import *
from capstone import CS_ARCH_X86, CS_GRP_CALL, CS_GRP_JUMP, CS_GRP_RET, CS_MODE_64, Cs
from capstone.x86 import X86_OP_IMM
from elftools.elf.elffile import ELFFile

# As you might guess this is 100% vibecoded, enjoy the slop

class ElfImage:
    def __init__(self, path):
        self.path = path
        self.segments = []

        with open(path, "rb") as f:
            elf = ELFFile(f)
            if elf.get_machine_arch() not in {"x86", "x64"}:
                raise ValueError("this demo only supports x86/x86-64 ELF files")

            self.entry = elf.header["e_entry"]
            mode = CS_MODE_64 if elf.elfclass == 64 else 0
            self.disasm = Cs(CS_ARCH_X86, mode)
            self.disasm.detail = True

            for segment in elf.iter_segments():
                if segment.header.p_type != "PT_LOAD":
                    continue
                self.segments.append((segment.header.p_vaddr, segment.data()))

    def bytes_from(self, addr):
        for base, data in self.segments:
            offset = addr - base
            if 0 <= offset < len(data):
                return data[offset:]
        return b""


def instruction_text(ins):
    if ins.op_str:
        return f"{ins.mnemonic} {ins.op_str}"
    return ins.mnemonic

def immediate_target(ins):
    if len(ins.operands) != 1 or ins.operands[0].type != X86_OP_IMM:
        return None
    return ins.operands[0].imm

def disassembler(binary: ElfImage, addr: int):
    ins = next(binary.disasm.disasm(binary.bytes_from(addr), addr, count=1), None)
    if ins is None:
        return Ret("invalid")

    text = instruction_text(ins)
    nexti = addr + ins.size

    if CS_GRP_RET in ins.groups:
        return Ret(text)

    target = immediate_target(ins)
    if CS_GRP_CALL in ins.groups and target is not None:
        return Call(nexti=nexti, target=target, s=text)

    if CS_GRP_JUMP in ins.groups:
        if target is None:
            if ins.mnemonic == "jmp":
                return Ret(s=text) # Non-immediate jump, stop analysis here
            else:
                return Instruction(nexti=nexti, s=text)
        if ins.mnemonic == "jmp":
            return Jump(target=target, s=text)
        return CondJump(cond_true=target, cond_false=nexti, s=text)

    return Instruction(nexti=nexti, s=text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Render a small x86/x86-64 ELF CFG demo.")
    parser.add_argument("path")
    parser.add_argument("--start", type=lambda value: int(value, 0), help="virtual address to start from")
    parser.add_argument("--output", default="CFG-x86")
    args = parser.parse_args()

    image = ElfImage(args.path)
    start = image.entry if args.start is None else args.start
    libcfg.CFG(image, disassembler, [start], directory=args.output)
