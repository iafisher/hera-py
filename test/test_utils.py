import pytest

from hera.utils import to_uint


def test_to_uint_with_min_negative():
    assert to_uint(-1) == 65535


def test_to_uint_with_max_negative():
    assert to_uint(-32768) == 32768


def test_to_uint_with_mid_sized_negative():
    assert to_uint(-1734) == 63802


def test_to_uint_with_another_negative():
    assert to_uint(-25043) == 40493


def test_to_uint_with_positive():
    assert to_uint(17) == 17


def test_to_uint_with_zero():
    assert to_uint(0) == 0


def test_to_uint_with_overflow():
    with pytest.raises(ValueError):
        to_uint(-32769)


def test_to_uint_with_another_overflow():
    with pytest.raises(ValueError):
        to_uint(-45000)


def test_to_uint_with_positive_overflow():
    # to_uint doesn't check positive overflow.
    assert to_uint(70000) == 70000
