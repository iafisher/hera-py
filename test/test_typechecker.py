import pytest

from lark import Token

from hera.parser import Op
from hera.typechecker import (
    check_types,
    typecheck,
    typecheck_one,
    REGISTER,
    REGISTER_OR_LABEL,
    U4,
    U16,
)
from hera.utils import HERAError, IntToken


def R(s):
    return Token("REGISTER", s)


def SYM(s=""):
    return Token("SYMBOL", s)


def test_check_types_with_too_few():
    errors = check_types(SYM(), [REGISTER, REGISTER], [R("R1")])
    assert len(errors) == 1
    assert "too few" in errors[0].msg


def test_check_types_with_too_many():
    errors = check_types(SYM(), [REGISTER], [R("R1"), IntToken(10)])
    assert len(errors) == 1
    assert "too many" in errors[0].msg


def test_check_types_with_wrong_type():
    errors = check_types(SYM(), [REGISTER], [IntToken(10)])
    assert len(errors) == 1
    assert "not a register" in errors[0].msg

    errors2 = check_types(SYM(), [U16], [R("R1")])
    assert len(errors2) == 1
    assert "not an integer" in errors2[0].msg


def test_check_types_with_u16_out_of_range():
    errors = check_types(SYM(), [U16], [IntToken(65536)])
    assert len(errors) == 1
    assert "out of range" in errors[0].msg


def test_check_types_with_negative_u16():
    errors = check_types(SYM(), [U16], [IntToken(-1)])
    assert len(errors) == 1
    assert "must not be negative" in errors[0].msg


def test_check_types_with_u4_out_of_range():
    errors = check_types(SYM(), [U4], [IntToken(16)])
    assert len(errors) == 1
    assert "out of range" in errors[0].msg

    errors2 = check_types(SYM(), [U4], [IntToken(-1)])
    assert len(errors2) == 1
    assert "must not be negative" in errors2[0].msg


def test_check_types_with_range_object():
    errors = check_types(SYM(), [range(-10, 10)], [IntToken(-11)])
    assert len(errors) == 1
    assert "out of range" in errors[0].msg

    errors2 = check_types(SYM(), [range(-10, 10)], [IntToken(10)])
    assert len(errors2) == 1
    assert "out of range" in errors2[0].msg

    errors3 = check_types(SYM(), [range(-10, 10)], [R("R1")])
    assert len(errors3) == 1
    assert "not an integer" in errors3[0].msg

    r = range(-10, 10)
    assert check_types("", [r, r, r], [5, -10, 9]) == []


def test_check_types_with_constant_symbol():
    assert check_types("", [range(0, 100)], [Token("SYMBOL", "n")]) == []


def test_check_types_with_register_or_label():
    assert check_types("", [REGISTER_OR_LABEL], [Token("SYMBOL", "n")]) == []
    assert check_types("", [REGISTER_OR_LABEL], [R("R1")]) == []


def test_typecheck_SET():
    assert typecheck_one(Op("SET", [R("R1"), 42])) == []
    assert typecheck_one(Op("SET", [R("R1"), 0xFFFF])) == []
    assert typecheck_one(Op("SET", [R("R1"), -0x7FFF])) == []


def test_typecheck_SETLO():
    assert typecheck_one(Op("SETLO", [R("R2"), 42])) == []
    assert typecheck_one(Op("SETLO", [R("R2"), 0xFF])) == []
    assert typecheck_one(Op("SETLO", [R("R2"), -0x7F])) == []


def test_typecheck_SETHI():
    assert typecheck_one(Op("SETHI", [R("R2"), 42])) == []
    assert typecheck_one(Op("SETHI", [R("R2"), 0xFF])) == []
    assert typecheck_one(Op("SETHI", [R("R2"), -0x7F])) == []


def test_typecheck_AND():
    assert typecheck_one(Op("AND", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_OR():
    assert typecheck_one(Op("OR", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_ADD():
    assert typecheck_one(Op("ADD", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_SUB():
    assert typecheck_one(Op("SUB", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_MUL():
    assert typecheck_one(Op("MUL", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_XOR():
    assert typecheck_one(Op("XOR", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_INC():
    assert typecheck_one(Op("INC", [R("R6"), 42])) == []
    assert typecheck_one(Op("INC", [R("R6"), 1])) == []
    assert typecheck_one(Op("INC", [R("R6"), 64])) == []


def test_typecheck_DEC():
    assert typecheck_one(Op("DEC", [R("R6"), 42])) == []
    assert typecheck_one(Op("DEC", [R("R6"), 1])) == []
    assert typecheck_one(Op("DEC", [R("R6"), 64])) == []


def test_typecheck_LSL():
    assert typecheck_one(Op("LSL", [R("R7"), R("R8")])) == []


def test_typecheck_LSR():
    assert typecheck_one(Op("LSR", [R("R7"), R("R8")])) == []


def test_typecheck_LSL8():
    assert typecheck_one(Op("LSL8", [R("R7"), R("R8")])) == []


def test_typecheck_LSR8():
    assert typecheck_one(Op("LSR8", [R("R7"), R("R8")])) == []


def test_typecheck_ASL():
    assert typecheck_one(Op("ASL", [R("R7"), R("R8")])) == []


def test_typecheck_ASR():
    assert typecheck_one(Op("ASR", [R("R7"), R("R8")])) == []


def test_typecheck_SAVEF():
    assert typecheck_one(Op("SAVEF", [R("R9")])) == []


def test_typecheck_RSTRF():
    assert typecheck_one(Op("RSTRF", [R("R9")])) == []


def test_typecheck_FON():
    assert typecheck_one(Op("FON", [0b10101])) == []
    assert typecheck_one(Op("FON", [0b01000])) == []
    assert typecheck_one(Op("FON", [0b11111])) == []
    assert typecheck_one(Op("FON", [0])) == []


def test_typecheck_FOFF():
    assert typecheck_one(Op("FOFF", [0b10101])) == []
    assert typecheck_one(Op("FOFF", [0b01000])) == []
    assert typecheck_one(Op("FOFF", [0b11111])) == []
    assert typecheck_one(Op("FOFF", [0])) == []


def test_typecheck_FSET5():
    assert typecheck_one(Op("FSET5", [0b10101])) == []
    assert typecheck_one(Op("FSET5", [0b01000])) == []
    assert typecheck_one(Op("FSET5", [0b11111])) == []
    assert typecheck_one(Op("FSET5", [0])) == []


def test_typecheck_FSET4():
    assert typecheck_one(Op("FSET4", [0b1010])) == []
    assert typecheck_one(Op("FSET4", [0b0100])) == []
    assert typecheck_one(Op("FSET4", [0b1111])) == []
    assert typecheck_one(Op("FSET4", [0])) == []


def test_typecheck_LOAD():
    assert typecheck_one(Op("LOAD", [R("R1"), 0, R("R2")])) == []
    assert typecheck_one(Op("LOAD", [R("R1"), 0b11111, R("R2")])) == []


def test_typecheck_STORE():
    assert typecheck_one(Op("STORE", [R("R1"), 0, R("R2")])) == []
    assert typecheck_one(Op("STORE", [R("R1"), 0b11111, R("R2")])) == []


def test_typecheck_CALL():
    assert typecheck_one(Op("CALL", [R("R12"), R("R11")])) == []
    assert typecheck_one(Op("CALL", [R("R12"), SYM("f")])) == []


def test_typecheck_RETURN():
    assert typecheck_one(Op("RETURN", [R("R12"), R("R11")])) == []
    assert typecheck_one(Op("RETURN", [R("R12"), SYM("f")])) == []


def test_typecheck_single_error():
    # Second argument to SETHI is out of range.
    program = [
        Op(SYM("SETLO"), [R("R1"), IntToken(10)]),
        Op(SYM("SETHI"), [R("R1"), IntToken(1000)]),
    ]

    errors = typecheck(program)

    assert len(errors) == 1
    assert "SETHI" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_typecheck_multiple_errors():
    program = [Op(SYM("ADD"), [R("R1"), IntToken(10)]), Op(SYM("INC"), [R("R3")])]

    errors = typecheck(program)

    assert len(errors) == 3

    assert "ADD" in errors[0].msg
    assert "too few" in errors[0].msg

    assert "ADD" in errors[1].msg
    assert "not a register" in errors[1].msg

    assert "INC" in errors[2].msg
    assert "too few" in errors[2].msg
