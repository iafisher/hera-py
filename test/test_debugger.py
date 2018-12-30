import pytest

from hera.debugger import Debugger
from hera.parser import parse
from hera.preprocessor import preprocess
from hera.symtab import get_symtab


@pytest.fixture
def debugger():
    return Debugger(SAMPLE_PROGRAM)


_tree = parse(
    """\
// A comment
SET(R1, 10)
SET(R2, 32)
ADD(R3, R1, R2)
"""
)
_symtab = get_symtab(_tree)
SAMPLE_PROGRAM = preprocess(_tree, _symtab)


def test_resolve_breakpoint(debugger):
    assert debugger.resolve_breakpoint(2) == 0


def test_resolve_breakpoint_out_of_range(debugger):
    with pytest.raises(ValueError) as e:
        debugger.resolve_breakpoint(10)
    assert "could not find corresponding line" in str(e)


def test_resolve_breakpoint_invalid_format(debugger):
    with pytest.raises(ValueError) as e:
        debugger.resolve_breakpoint("a")
    assert "could not parse argument" in str(e)


def test_get_breakpoint_name(debugger):
    # Zero'th instruction corresponds to second line.
    assert debugger.get_breakpoint_name(0) == "2"


def test_print_current_op(debugger, capsys):
    debugger.print_current_op()

    captured = capsys.readouterr()
    assert captured.out == "0000  SET(R1, 10)\n"
