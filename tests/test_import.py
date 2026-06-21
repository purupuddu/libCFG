import libcfg
import graphviz
from libcfg import CFG, Call, CondJump, Instruction, Jump, Ret


def test_import() -> None:
    assert libcfg.__version__ == "0.1.0"
    assert graphviz.Digraph is not None
    assert libcfg.CFG is CFG
    assert libcfg.Instruction is Instruction
    assert libcfg.Call is Call
    assert libcfg.Jump is Jump
    assert libcfg.CondJump is CondJump
    assert libcfg.Ret is Ret
