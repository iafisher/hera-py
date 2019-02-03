import pytest

from hera.data import HERAError
from hera.utils import (
    align_caret,
    format_int,
    from_u16,
    make_ansi,
    register_to_index,
    to_u16,
    to_u32,
)


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
    with pytest.raises(HERAError):
        to_u16(-32769)


def test_to_u16_with_another_overflow():
    with pytest.raises(HERAError):
        to_u16(-45000)


def test_to_u16_with_positive_overflow():
    with pytest.raises(HERAError):
        to_u16(65536)


def test_to_u16_with_another_positive_overflow():
    with pytest.raises(HERAError):
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
    with pytest.raises(HERAError):
        to_u32(-2147483649)


def test_to_u32_with_another_overflow():
    with pytest.raises(HERAError):
        to_u32(-3000000000)


def test_to_u32_with_positive_overflow():
    with pytest.raises(HERAError):
        to_u32(4294967296)


def test_to_u32_with_another_positive_overflow():
    with pytest.raises(HERAError):
        to_u32(5000000000)


def test_register_to_index_with_numbered_registers():
    for i in range(0, 16):
        assert register_to_index("R" + str(i)) == i
        assert register_to_index("r" + str(i)) == i


def test_register_to_index_with_named_registers():
    assert register_to_index("FP") == 14
    assert register_to_index("fp") == 14
    assert register_to_index("SP") == 15
    assert register_to_index("sp") == 15
    assert register_to_index("Rt") == 11
    assert register_to_index("rt") == 11
    assert register_to_index("PC_ret") == 13
    assert register_to_index("pc_ret") == 13
    assert register_to_index("FP_alt") == 12
    assert register_to_index("fp_alt") == 12


def test_register_to_index_with_invalid_register():
    with pytest.raises(HERAError) as e:
        register_to_index("R16")
    assert "R16" in str(e)


def test_align_caret():
    assert align_caret("\t\t  a", 5) == "\t\t  "


def test_make_ansi_red():
    assert make_ansi(31, 1) == "\033[31;1m"


def test_make_ansi_reset():
    assert make_ansi(0) == "\033[0m"


def test_format_int_with_small_positive():
    assert format_int(5) == "0x0005 = 5"


def test_format_int_with_ASCII_value():
    assert format_int(65) == "0x0041 = 65 = 'A'"


def test_format_int_with_large_positive():
    assert format_int(4000) == "0x0fa0 = 4000"


def test_format_int_with_negative():
    assert format_int(65535) == "0xffff = 65535 = -1"


def test_format_int_with_non_default_format():
    assert format_int(2, spec="bds") == "0b0000000000000010 = 2"
