from libcfg import CFG
from libcfg.Instruction import *

def disassembler(bin:bytes, addr:int):
    op = bin[addr:addr+2]
    opi = op[0]<<8 | op[1]
    
    if op == b"\x00\xee":
        return Ret()
    if op == b"\x00\xfd":
        return Ret(f"exit")
    
    if opi & 0xf000 == 0x1000:
        return Jump(opi & 0xfff)
    if opi & 0xf000 == 0x2000:
        return Call(addr+2, opi & 0xfff)
    if 0x3000 <= (opi & 0xf000) <= 0x5000:
        return CondJump(cond_true=addr+4, cond_false=addr+2)
    return Instruction(addr+2)



CFG.CFG(bytes(0x200) + open("main.bin", "rb").read(), disassembler, [0x200])
