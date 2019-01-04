import pytest
from unittest.mock import patch

from hera.data import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_aslu_op_with_ADD(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = 1

    vm.exec_aslu_op(Op("ADD", ["R1", "R2", "R3"]))

    assert vm.pc == 1
    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_exec_aslu_op_with_SUB(vm):
    vm.flag_carry_block = True
    vm.registers[2] = 40
    vm.registers[3] = 100

    vm.exec_aslu_op(Op("SUB", ["R1", "R2", "R3"]))

    assert vm.pc == 1
    assert vm.registers[1] == to_u16(-60)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_calculate_ADD_small_numbers(vm):
    assert vm.calculate_ADD(20, 22) == 42
    assert not vm.flag_overflow
    assert not vm.flag_carry


def test_calculate_ADD_with_negative(vm):
    assert vm.calculate_ADD(to_u16(-14), 8) == to_u16(-6)


def test_calculate_ADD_with_zero(vm):
    assert vm.calculate_ADD(to_u16(-4), 4) == 0


def test_calculate_ADD_with_overflow(vm):
    assert vm.calculate_ADD(32767, 1) == to_u16(-32768)
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_calculate_ADD_with_big_overflow(vm):
    assert vm.calculate_ADD(32767, 32767) == to_u16(-2)
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_calculate_ADD_with_negative_overflow(vm):
    assert vm.calculate_ADD(to_u16(-32768), to_u16(-32768)) == 0
    assert vm.flag_overflow
    assert vm.flag_carry


def test_calculate_ADD_with_carry(vm):
    vm.flag_carry = True
    assert vm.calculate_ADD(5, 3) == 9
    assert not vm.flag_carry


def test_calculate_ADD_with_carry_and_block(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    assert vm.calculate_ADD(5, 3) == 8
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_calculate_ADD_with_overflow_from_carry(vm):
    vm.flag_carry = True
    assert vm.calculate_ADD(32760, 7) == to_u16(-32768)
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_calculate_SUB_small_numbers(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(64, 22) == 42


def test_calculate_SUB_sets_flags(vm):
    vm.flag_carry_block = True
    vm.calculate_SUB(64, 22)
    assert not vm.flag_overflow
    assert vm.flag_carry


def test_calculate_SUB_with_negative(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(to_u16(-64), 22) == to_u16(-86)


def test_calculate_SUB_with_zero(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(to_u16(-37), to_u16(-37)) == 0


def test_calculate_SUB_with_two_negatives(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(to_u16(-20), to_u16(-40)) == 20
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_calculate_SUB_with_min_negative_overflow(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(to_u16(-32768), 1) == 32767
    assert vm.flag_carry
    assert vm.flag_overflow


def test_calculate_SUB_with_big_negative_overflow(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(to_u16(-32000), 32000) == 1536
    assert vm.flag_carry
    assert vm.flag_overflow


def test_calculate_SUB_with_max_negative_overflow(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(to_u16(-32768), 32767) == 1
    assert vm.flag_carry
    assert vm.flag_overflow


def test_calculate_SUB_with_min_positive_overflow(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(32767, to_u16(-1)) == to_u16(-32768)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_calculate_SUB_with_big_positive_overflow(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(27500, to_u16(-7040)) == to_u16(-30996)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_calculate_SUB_with_max_positive_overflow(vm):
    vm.flag_carry_block = True
    assert vm.calculate_SUB(32767, to_u16(-32768)) == to_u16(-1)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_calculate_SUB_with_implicit_borrow(vm):
    assert vm.calculate_SUB(17, 5) == 11


def test_calculate_SUB_with_no_carry_block_and_no_borrow(vm):
    vm.flag_carry = True
    assert vm.calculate_SUB(to_u16(-64), 22) == to_u16(-86)
    assert vm.flag_carry


def test_calculate_SUB_overflow_from_borrow(vm):
    assert vm.calculate_SUB(to_u16(-32767), 1) == 32767
    assert vm.flag_carry
    assert vm.flag_overflow


def test_calculate_SUB_overflow_takes_borrow_into_account(vm):
    vm.calculate_SUB(10, 11)
    assert not vm.flag_overflow


def test_calculate_SUB_sets_carry_for_equal_operands(vm):
    vm.flag_carry = True
    assert vm.calculate_SUB(12, 12) == 0
    assert vm.flag_carry


def test_calculate_MUL_with_small_positives(vm):
    assert vm.calculate_MUL(4, 2) == 8


def test_calculate_MUL_with_large_positives(vm):
    assert vm.calculate_MUL(4500, 3) == 13500


def test_calculate_MUL_with_small_negatives(vm):
    assert vm.calculate_MUL(to_u16(-5), 3) == to_u16(-15)


def test_calculate_MUL_with_large_negatives(vm):
    assert vm.calculate_MUL(7, to_u16(-3100)) == to_u16(-21700)


def test_calculate_MUL_with_signed_positive_overflow(vm):
    assert vm.calculate_MUL(17000, 3) == to_u16(-14536)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_calculate_MUL_with_unsigned_positive_overflow(vm):
    assert vm.calculate_MUL(128, 749) == 30336
    assert vm.flag_carry
    assert vm.flag_overflow


def test_calculate_MUL_with_signed_negative_overflow(vm):
    assert vm.calculate_MUL(to_u16(-400), to_u16(-200)) == 14464
    assert vm.flag_carry
    assert vm.flag_overflow


def test_calculate_MUL_ignores_carry_when_blocked(vm):
    vm.flag_carry_block = True
    vm.flag_carry = True
    assert vm.calculate_MUL(4, 12) == 48
    assert not vm.flag_carry


def test_calculate_MUL_ignores_carry_when_not_blocked(vm):
    vm.flag_carry = True
    assert vm.calculate_MUL(4, 12) == 48
    assert not vm.flag_carry


def test_calculate_MUL_produces_high_bits_when_sign_flag_is_on(vm):
    vm.flag_sign = True
    assert vm.calculate_MUL(20000, 200) == 0b111101
    # TODO: Find out how the carry and overflow flags should be set.


def test_calculate_MUL_with_sign_flag_and_negative_result(vm):
    vm.flag_sign = True
    assert vm.calculate_MUL(20000, to_u16(-200)) == 0b1111111111000010


def test_calculate_MUL_ignores_sign_flag_when_carry_is_blocked(vm):
    vm.flag_sign = True
    vm.flag_carry_block = True
    assert vm.calculate_MUL(20000, 200) == 2304
    assert vm.flag_carry


def test_calculate_AND_same_numbers(vm):
    assert vm.calculate_AND(27, 27) == 27


def test_calculate_AND_different_numbers(vm):
    assert vm.calculate_AND(0b011, 0b110) == 0b010


def test_calculate_AND_big_numbers(vm):
    assert vm.calculate_AND(62434, 17589) == 16544


def test_calculate_AND_does_not_set_other_flags(vm):
    assert vm.calculate_AND(to_u16(-1), to_u16(-1)) == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_calculate_AND_does_not_clear_other_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.calculate_AND(to_u16(-1), to_u16(-1))
    assert vm.flag_carry
    assert vm.flag_overflow


def test_calculate_OR_same_numbers(vm):
    assert vm.calculate_OR(27, 27) == 27


def test_calculate_OR_different_numbers(vm):
    assert vm.calculate_OR(0b011, 0b110) == 0b111


def test_calculate_OR_big_numbers(vm):
    assert vm.calculate_OR(8199, 762) == 8959


def test_calculate_OR_does_not_set_other_flags(vm):
    assert vm.calculate_OR(to_u16(-1), to_u16(-1)) == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_calculate_OR_does_not_clear_other_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.calculate_OR(to_u16(-1), to_u16(-1))
    assert vm.flag_carry
    assert vm.flag_overflow


def test_calculate_XOR_same_numbers(vm):
    assert vm.calculate_XOR(27, 27) == 0


def test_calculate_XOR_different_numbers(vm):
    assert vm.calculate_XOR(0b011, 0b110) == 0b101


def test_calculate_XOR_big_numbers(vm):
    assert vm.calculate_XOR(8199, 762) == 8957


def test_calculate_XOR_does_not_set_other_flags(vm):
    assert vm.calculate_XOR(0, to_u16(-37)) == to_u16(-37)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_calculate_XOR_does_not_clear_other_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.calculate_XOR(0, to_u16(-37))
    assert vm.flag_carry
    assert vm.flag_overflow
