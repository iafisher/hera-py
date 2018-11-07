import pytest

from hera.utils import from_uint, to_u32, to_uint


def test_to_uint_with_max_negative():
    assert to_uint(-1) == 65535


def test_to_uint_with_min_negative():
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


def test_from_uint_with_min_negative():
    assert from_uint(65535) == -1


def test_from_uint_with_max_negative():
    assert from_uint(32768) == -32768


def test_from_uint_with_mid_sized_negative():
    assert from_uint(63802) == -1734


def test_from_uint_with_another_negative():
    assert from_uint(40493) == -25043


def test_from_uint_with_positive():
    assert from_uint(17) == 17


def test_from_uint_with_zero():
    assert from_uint(0) == 0


def test_to_u32_with_small_positive():
    assert to_u32(7) == 7


def test_to_u32_with_large_positive():
    assert to_u32(100000) == 100000


def test_to_u32_with_small_negative():
    assert to_u32(-17) == 4294967279


def test_to_u32_with_max_negative():
    assert to_u32(-1) == 4294967295


def test_to_u32_with_min_negative():
    assert to_u32(-2147483648) == 2147483648


def test_to_u32_with_large_negative():
    assert to_u32(-128000) == 4294839296


def test_to_u32_with_zero():
    assert to_u32(0) == 0


def test_to_u32_with_overflow():
    with pytest.raises(ValueError):
        to_u32(-2147483649)


def test_to_u32_with_another_overflow():
    with pytest.raises(ValueError):
        to_u32(-3000000000)


def test_to_u32_with_positive_overflow():
    # to_u32 doesn't check positive overflow.
    assert to_uint(3000000000) == 3000000000
