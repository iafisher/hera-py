import pytest

from lark import Token

from hera.parser import Op
from hera.typechecker import (
    check_types,
    typecheck,
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
