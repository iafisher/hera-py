from hera.main import (
    align_caret,
    dump_state,
    op_to_string,
    program_to_string,
)
from hera.parser import Op
from hera.vm import VirtualMachine



def test_op_to_string():
    assert op_to_string(Op("SET", ["R1", "top"])) == "SET(R1, top)"


def test_op_to_string_with_integer():
    assert op_to_string(Op("INC", ["R7", 12])) == "INC(R7, 12)"


def test_program_to_string():
    program = [
        Op("SET", ["R1", 20]),
        Op("SET", ["R2", 22]),
        Op("ADD", ["R3", "R1", "R2"]),
    ]
    assert program_to_string(program) == "SET(R1, 20)\nSET(R2, 22)\nADD(R3, R1, R2)"


def test_align_caret():
    assert align_caret("\t\t  a", 5) == "\t\t  "


def test_dump_state(capsys):
    dump_state(VirtualMachine())

    captured = capsys.readouterr()
    assert "R1  = 0x0000 = 0" in captured.err
    assert "R7  = 0x0000 = 0" in captured.err
    assert "R14 = 0x0000 = 0" in captured.err
    assert "Zero flag is OFF" in captured.err
    assert "Sign flag is OFF" in captured.err
    assert "Overflow flag is OFF" in captured.err
    assert "Carry flag is OFF" in captured.err
    assert "Carry block flag is OFF" in captured.err
