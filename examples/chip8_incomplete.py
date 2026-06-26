from libcfg import *

# uses padding to have consistent addresses
bin = bytes(0x200) + open("main.bin", "rb").read()

def disassembler(addr:int):
    """Minimal chip8 example. Only disassembles what's relevant for cfg generation.
    Any other instruction will be named "TEMP"
    """
    global bin

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
        # This is a simple way of grouping "conditional skip" instructions
        # additional casework to distinguish the condition+parameters of the skip is missing
        return CondJump(cond_true=addr+4, cond_false=addr+2) # condjump models skip instructions
    # other instructions which are not relevant to the CFG should be handled here 
    return Instruction(addr+2, s="...")

# main.bin from THEM?!CTF 2026
CFG(disassembler, [0x200], directory="CFG-chip8")
