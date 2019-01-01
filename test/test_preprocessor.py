import pytest
from unittest.mock import patch

from hera.parser import Op, Token
from hera.preprocessor import convert, convert_set, preprocess, substitute_label


def R(s):
    return Token("REGISTER", s)


def SYM(s):
    return Token("SYMBOL", s)


def test_substitute_label_with_SETLO():
    labels = {"N": 10}
    assert substitute_label(Op(SYM("SETLO"), [R("R1"), SYM("N")]), labels) == Op(
        "SETLO", ["R1", 10]
    )


def test_substitute_label_with_SETHI():
    labels = {"N": 10}
    assert substitute_label(Op(SYM("SETHI"), [R("R1"), SYM("N")]), labels) == Op(
        "SETHI", ["R1", 10]
    )


def test_substitute_label_with_other_op():
    labels = {"N": 10}
    assert substitute_label(Op(SYM("INC"), [R("R1"), SYM("N")]), labels) == Op(
        "INC", ["R1", 10]
    )


def test_convert_set_with_small_positive():
    assert convert_set("R5", 18) == [Op("SETLO", ["R5", 18]), Op("SETHI", ["R5", 0])]


def test_convert_set_with_large_positive():
    assert convert_set("R5", 34000) == [
        Op("SETLO", ["R5", 208]),
        Op("SETHI", ["R5", 132]),
    ]


def test_convert_set_with_negative():
    assert convert_set("R5", -5) == [Op("SETLO", ["R5", 251]), Op("SETHI", ["R5", 255])]


def test_convert_set_with_symbol():
    assert convert_set("R5", "whatever") == [
        Op("SETLO", ["R5", "whatever"]),
        Op("SETHI", ["R5", "whatever"]),
    ]


def test_convert_move():
    assert convert(Op("MOVE", ["R5", "R3"])) == [Op("OR", ["R5", "R3", "R0"])]


def test_convert_con():
    assert convert(Op("CON", [])) == [Op("FON", [8])]


def test_convert_coff():
    assert convert(Op("COFF", [])) == [Op("FOFF", [8])]


def test_convert_cbon():
    assert convert(Op("CBON", [])) == [Op("FON", [16])]


def test_convert_ccboff():
    assert convert(Op("CCBOFF", [])) == [Op("FOFF", [24])]


def test_convert_cmp():
    assert convert(Op("CMP", ["R1", "R2"])) == [
        Op("FON", [8]),
        Op("SUB", ["R0", "R1", "R2"]),
    ]


def test_convert_setrf_with_small_positive():
    assert convert(Op("SETRF", ["R5", 18])) == [
        Op("SETLO", ["R5", 18]),
        Op("SETHI", ["R5", 0]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_convert_setrf_with_large_positive():
    assert convert(Op("SETRF", ["R5", 34000])) == [
        Op("SETLO", ["R5", 208]),
        Op("SETHI", ["R5", 132]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_convert_setrf_with_negative():
    assert convert(Op("SETRF", ["R5", -5])) == [
        Op("SETLO", ["R5", 251]),
        Op("SETHI", ["R5", 255]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_convert_flags():
    assert convert(Op("FLAGS", ["R8"])) == [
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R8", "R0"]),
    ]


def test_convert_halt():
    assert convert(Op("HALT", [])) == [Op("BRR", [0])]


def test_convert_nop():
    assert convert(Op("NOP", [])) == [Op("BRR", [1])]


def test_convert_call_with_register():
    assert convert(Op("CALL", ["R12", R("R13")])) == [Op("CALL", ["R12", "R13"])]


def test_convert_call_with_label():
    assert convert(Op("CALL", ["R12", Token("SYMBOL", "div")])) == [
        Op("SETLO", ["R13", "div"]),
        Op("SETHI", ["R13", "div"]),
        Op("CALL", ["R12", "R13"]),
    ]


def test_convert_neg():
    assert convert(Op("NEG", ["R1", "R2"])) == [
        Op("FON", [8]),
        Op("SUB", ["R1", "R0", "R2"]),
    ]


def test_convert_not():
    assert convert(Op("NOT", ["R1", "R2"])) == [
        Op("SETLO", ["R11", 0xFF]),
        Op("SETHI", ["R11", 0xFF]),
        Op("XOR", ["R1", "R11", "R2"]),
    ]


def test_preprocess_constant():
    program = [Op(Token("SYMBOL", "SET"), [R("R1"), Token("SYMBOL", "n")])]
    assert preprocess(program, {"n": 100}) == [
        Op("SETLO", ["R1", 100]),
        Op("SETHI", ["R1", 0]),
    ]
