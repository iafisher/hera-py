import pytest

from hera.utils import from_u16, to_u16, to_u32


def test_to_u16_with_max_negative():
    assert to_u16(-1) == 65535


def test_to_u16_with_min_negative():
    assert to_u16(-32768) == 32768


def test_to_u16_with_mid_sized_negative():
    assert to_u16(-1734) == 63802


def test_to_u16_with_another_negative():
    assert to_u16(-25043) == 40493


def test_to_u16_with_positive():
    assert to_u16(17) == 17


def test_to_u16_with_max_positive():
    assert to_u16(65535) == 65535


def test_to_u16_with_zero():
    assert to_u16(0) == 0


def test_to_u16_with_overflow():
    with pytest.raises(OverflowError):
        to_u16(-32769)


def test_to_u16_with_another_overflow():
    with pytest.raises(OverflowError):
        to_u16(-45000)


def test_to_u16_with_positive_overflow():
    with pytest.raises(OverflowError):
        to_u16(65536)


def test_to_u16_with_another_positive_overflow():
    with pytest.raises(OverflowError):
        to_u16(70000)


def test_from_u16_with_min_negative():
    assert from_u16(65535) == -1


def test_from_u16_with_max_negative():
    assert from_u16(32768) == -32768


def test_from_u16_with_mid_sized_negative():
    assert from_u16(63802) == -1734


def test_from_u16_with_another_negative():
    assert from_u16(40493) == -25043


def test_from_u16_with_positive():
    assert from_u16(17) == 17


def test_from_u16_with_zero():
    assert from_u16(0) == 0


def test_to_u32_with_small_positive():
    assert to_u32(7) == 7


def test_to_u32_with_large_positive():
    assert to_u32(100000) == 100000


def test_to_u32_with_max_positive():
    assert to_u32(4294967295) == 4294967295


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
    with pytest.raises(OverflowError):
        to_u32(-2147483649)


def test_to_u32_with_another_overflow():
    with pytest.raises(OverflowError):
        to_u32(-3000000000)


def test_to_u32_with_positive_overflow():
    with pytest.raises(OverflowError):
        to_u32(4294967296)


def test_to_u32_with_another_positive_overflow():
    with pytest.raises(OverflowError):
        to_u32(5000000000)
