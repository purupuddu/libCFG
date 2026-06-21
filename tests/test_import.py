import libcfg
import graphviz


def test_import() -> None:
    assert libcfg.__version__ == "0.1.0"
    assert graphviz.Digraph is not None
