from typing import List


class BaseInstruction:
    def nextis(self) -> List[int]:
        self.s = "BASE"
        return []

    def arrs(self) -> List[dict]:
        return []

class Instruction(BaseInstruction):
    """A generic instruction with no impact on control flow.
    Can be a mov, add, xor, or any instruction unrelated to control flow.
    Nexti is the address of the next instruction"""

    def __init__(self, nexti, s="TEMP"):
        self.nexti = nexti
        self.s = s

    def nextis(self) -> List[int]:
        return [self.nexti]

    def arrs(self):
        return [{"color":"black", "to":self.nexti}]


class Ret(BaseInstruction):
    """Models a return instruction, or any instruction with no next. 
    Might also be used to model an exit instruction"""

    def __init__(self, s="ret"):
        self.s = s

    def nextis(self) -> List[int]:
        return []

class Jump(BaseInstruction):
    """Models any unconditional jump instruction. The target must be a immediate value"""

    def __init__(self, target, s=None):
        self.target = target
        self.s = s
        if s is None:
            self.s = f"jmp loc_{target:x}"

    def nextis(self) -> List[int]:
        return [self.target]

    def arrs(self):
        return [{"color":"blue", "to":self.target}]

class CondJump(BaseInstruction):
    """Models any conditional jump instruction, has two possible successor nodes.
    The targets must both be immediate values"""

    def __init__(self, cond_true, cond_false, s=None):
        self.cond_true = cond_true
        self.cond_false = cond_false
        self.s = s
        if s is None:
            self.s = f"jmpcond loc_{cond_true:x}"

    def nextis(self) -> List[int]:
        return [self.cond_true, self.cond_false]

    def arrs(self):
        return [{"color":"green", "to":self.cond_true}, {"color":"red", "to":self.cond_false}]

class Call(BaseInstruction):
    """Models call <target> instructions. The target must be a immediate value"""

    def __init__(self, nexti, target, s="call"):
        self.nexti = nexti
        self.target = target
        self.s = s

    def nextis(self) -> List[int]:
        return [self.nexti]

    def arrs(self):
        return [{"color":"black", "to":self.nexti}]
