from hera.main import make_ansi, op_to_string, program_to_string
from hera.parser import Op


def test_make_ansi_red():
    assert make_ansi(31, 1) == "\033[31;1m"


def test_make_ansi_reset():
    assert make_ansi(0) == "\033[0m"


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
