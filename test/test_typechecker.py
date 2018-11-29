import pytest

from lark import Token

from hera.typechecker import check_types, REGISTER, REGISTER_OR_LABEL, U4, U16
from hera.utils import HERAError, IntToken


def R(s):
    return Token("REGISTER", s)


def test_check_types_with_too_few():
    with pytest.raises(HERAError) as e:
        check_types("", [REGISTER, REGISTER], [R("R1")])
    assert "too few" in str(e)


def test_check_types_with_too_many():
    with pytest.raises(HERAError) as e:
        check_types("", [REGISTER], [R("R1"), IntToken(10)])
    assert "too many" in str(e)


def test_check_types_with_wrong_type():
    with pytest.raises(HERAError) as e1:
        check_types("", [REGISTER], [IntToken(10)])
    assert "not a register" in str(e1)

    with pytest.raises(HERAError) as e2:
        check_types("", [U16], [R("R1")])
    assert "not an integer" in str(e2)


def test_check_types_with_u16_out_of_range():
    with pytest.raises(HERAError) as e:
        check_types("", [U16], [IntToken(65536)])
    assert "out of range" in str(e)


def test_check_types_with_negative_u16():
    with pytest.raises(HERAError) as e:
        check_types("", [U16], [IntToken(-1)])
    assert "must not be negative" in str(e)


def test_check_types_with_u4_out_of_range():
    with pytest.raises(HERAError) as e1:
        check_types("", [U4], [IntToken(16)])
    assert "out of range" in str(e1)

    with pytest.raises(HERAError) as e2:
        check_types("", [U4], [IntToken(-1)])
    assert "must not be negative" in str(e2)


def test_check_types_with_range_object():
    with pytest.raises(HERAError) as e1:
        check_types("", [range(-10, 10)], [IntToken(-11)])
    assert "out of range" in str(e1)

    with pytest.raises(HERAError) as e2:
        check_types("", [range(-10, 10)], [IntToken(10)])
    assert "out of range" in str(e2)

    with pytest.raises(HERAError) as e3:
        check_types("", [range(-10, 10)], [R("R1")])
    assert "not an integer" in str(e3)

    r = range(-10, 10)
    check_types("", [r, r, r], [5, -10, 9])


def test_check_types_with_constant_symbol():
    check_types("", [range(0, 100)], [Token("SYMBOL", "n")])


def test_check_types_with_register_or_label():
    check_types("", [REGISTER_OR_LABEL], [Token("SYMBOL", "n")])
    check_types("", [REGISTER_OR_LABEL], [R("R1")])
