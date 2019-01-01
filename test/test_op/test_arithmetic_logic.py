import pytest
from unittest.mock import patch

from hera.data import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_add(vm):
    with patch("hera.vm.VirtualMachine.exec_add") as mock_exec_add:
        vm.exec_one(Op("ADD", ["R1", "R2", "R3"]))
        assert mock_exec_add.call_count == 1
        assert mock_exec_add.call_args == (("R1", "R2", "R3"), {})


def test_add_small_numbers(vm):
    vm.registers[2] = 20
    vm.registers[3] = 22
    vm.exec_add("R1", "R2", "R3")
    assert vm.registers[1] == 42


def test_add_increments_pc(vm):
    vm.exec_add("R1", "R2", "R3")
    assert vm.pc == 1


def test_add_sets_flags(vm):
    vm.registers[2] = 20
    vm.registers[3] = 22
    vm.exec_add("R1", "R2", "R3")
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_negative(vm):
    vm.registers[2] = to_u16(-14)
    vm.registers[3] = 8
    vm.exec_add("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-6)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_add_with_zero(vm):
    vm.registers[7] = to_u16(-4)
    vm.registers[3] = 4
    vm.exec_add("R5", "R7", "R3")
    assert vm.registers[5] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_add_with_overflow(vm):
    vm.registers[9] = 32767
    vm.registers[2] = 1
    vm.exec_add("R7", "R9", "R2")
    assert vm.registers[7] == to_u16(-32768)
    assert vm.flag_sign
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_big_overflow(vm):
    vm.registers[9] = 32767
    vm.registers[2] = 32767
    vm.exec_add("R7", "R9", "R2")
    assert vm.registers[7] == to_u16(-2)
    assert vm.flag_sign
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_negative_overflow(vm):
    vm.registers[9] = to_u16(-32768)
    vm.registers[2] = to_u16(-32768)
    vm.exec_add("R7", "R9", "R2")
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry


def test_add_with_carry(vm):
    vm.registers[3] = 5
    vm.registers[5] = 3
    vm.flag_carry = True
    vm.exec_add("R7", "R3", "R5")
    assert vm.registers[7] == 9
    assert not vm.flag_carry


def test_add_with_carry_and_block(vm):
    vm.registers[3] = 5
    vm.registers[5] = 3
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_add("R7", "R3", "R5")
    assert vm.registers[7] == 8
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_add_with_overflow_from_carry(vm):
    vm.registers[2] = 32760
    vm.registers[3] = 7
    vm.flag_carry = True
    vm.exec_add("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-32768)
    assert vm.flag_sign
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_does_not_change_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 1
    vm.exec_add("R0", "R1", "R2")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_sub(vm):
    with patch("hera.vm.VirtualMachine.exec_sub") as mock_exec_sub:
        vm.exec_one(Op("SUB", ["R1", "R2", "R3"]))
        assert mock_exec_sub.call_count == 1
        assert mock_exec_sub.call_args == (("R1", "R2", "R3"), {})


def test_sub_small_numbers(vm):
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.flag_carry_block = True
    vm.exec_sub("R1", "R2", "R3")
    assert vm.registers[1] == 42


def test_sub_sets_flags(vm):
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.flag_carry_block = True
    vm.exec_sub("R1", "R2", "R3")
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry


def test_sub_increments_pc(vm):
    vm.exec_sub("R1", "R2", "R3")
    assert vm.pc == 1


def test_sub_with_negative(vm):
    vm.registers[2] = to_u16(-64)
    vm.registers[3] = 22
    vm.flag_carry_block = True
    vm.exec_sub("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-86)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_sub_with_zero(vm):
    vm.registers[2] = to_u16(-37)
    vm.registers[3] = to_u16(-37)
    vm.flag_carry_block = True
    vm.exec_sub("R1", "R2", "R3")
    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_sub_with_two_negatives(vm):
    vm.registers[2] = to_u16(-20)
    vm.registers[3] = to_u16(-40)
    vm.flag_carry_block = True
    vm.exec_sub("R1", "R2", "R3")
    assert vm.registers[1] == 20
    assert not vm.flag_sign
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_sub_with_min_negative_overflow(vm):
    vm.registers[1] = to_u16(-32768)
    vm.registers[2] = 1
    vm.flag_carry_block = True
    vm.exec_sub("R3", "R1", "R2")
    assert vm.registers[3] == 32767
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_big_negative_overflow(vm):
    vm.registers[1] = to_u16(-32000)
    vm.registers[2] = 32000
    vm.flag_carry_block = True
    vm.exec_sub("R3", "R1", "R2")
    assert vm.registers[3] == 1536
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_max_negative_overflow(vm):
    vm.registers[1] = to_u16(-32768)
    vm.registers[2] = 32767
    vm.flag_carry_block = True
    vm.exec_sub("R3", "R1", "R2")
    assert vm.registers[3] == 1
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_min_positive_overflow(vm):
    vm.registers[4] = 32767
    vm.registers[5] = to_u16(-1)
    vm.flag_carry_block = True
    vm.exec_sub("R6", "R4", "R5")
    assert vm.registers[6] == to_u16(-32768)
    assert vm.flag_sign
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_big_positive_overflow(vm):
    vm.registers[4] = 27500
    vm.registers[5] = to_u16(-7040)
    vm.flag_carry_block = True
    vm.exec_sub("R6", "R4", "R5")
    assert vm.registers[6] == to_u16(-30996)
    assert vm.flag_sign
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_max_positive_overflow(vm):
    vm.registers[4] = 32767
    vm.registers[5] = to_u16(-32768)
    vm.flag_carry_block = True
    vm.exec_sub("R6", "R4", "R5")
    assert vm.registers[6] == to_u16(-1)
    assert vm.flag_sign
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_implicit_borrow(vm):
    vm.registers[2] = 17
    vm.registers[3] = 5
    vm.exec_sub("R1", "R2", "R3")
    assert vm.registers[1] == 11


def test_sub_with_no_carry_block_and_no_borrow(vm):
    vm.registers[2] = to_u16(-64)
    vm.registers[3] = 22
    vm.flag_carry = True
    vm.exec_sub("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-86)
    assert vm.flag_carry


def test_sub_overflow_from_borrow(vm):
    vm.registers[1] = to_u16(-32767)
    vm.registers[2] = 1
    vm.exec_sub("R3", "R1", "R2")
    assert vm.registers[3] == 32767
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_overflow_takes_borrow_into_account(vm):
    vm.registers[1] = 10
    vm.registers[2] = 11
    vm.exec_sub("R0", "R1", "R2")
    assert not vm.flag_overflow


def test_sub_sets_carry_for_equal_operands(vm):
    vm.flag_carry = True
    vm.registers[1] = 12
    vm.registers[2] = 12
    vm.exec_sub("R3", "R1", "R2")
    assert vm.registers[3] == 0
    assert vm.flag_carry


def test_sub_does_not_affect_R0(vm):
    vm.registers[1] = 4
    vm.registers[2] = 3
    vm.exec_sub("R0", "R1", "R2")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_mul(vm):
    with patch("hera.vm.VirtualMachine.exec_mul") as mock_exec_mul:
        vm.exec_one(Op("MUL", ["R1", "R2", "R3"]))
        assert mock_exec_mul.call_count == 1
        assert mock_exec_mul.call_args == (("R1", "R2", "R3"), {})


def test_mul_with_small_positives(vm):
    vm.registers[2] = 4
    vm.registers[3] = 2
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 8


def test_mul_with_large_positives(vm):
    vm.registers[2] = 4500
    vm.registers[3] = 3
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 13500


def test_mul_with_small_negatives(vm):
    vm.registers[2] = to_u16(-5)
    vm.registers[3] = 3
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-15)


def test_mul_with_large_negatives(vm):
    vm.registers[2] = 7
    vm.registers[3] = to_u16(-3100)
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-21700)


def test_mul_sets_zero_flag(vm):
    vm.registers[2] = 7
    vm.registers[3] = 0
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_mul_sets_sign_flag(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = 17
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-17)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_mul_with_signed_positive_overflow(vm):
    vm.registers[2] = 17000
    vm.registers[3] = 3
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-14536)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_mul_with_unsigned_positive_overflow(vm):
    vm.registers[2] = 128
    vm.registers[3] = 749
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 30336
    assert vm.flag_carry
    assert vm.flag_overflow


def test_mul_with_signed_negative_overflow(vm):
    vm.registers[2] = to_u16(-400)
    vm.registers[3] = to_u16(-200)
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 14464
    assert vm.flag_carry
    assert vm.flag_overflow


def test_mul_ignores_carry_when_blocked(vm):
    vm.flag_carry_block = True
    vm.flag_carry = True
    vm.registers[2] = 4
    vm.registers[3] = 12
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 48
    assert not vm.flag_carry


def test_mul_ignores_carry_when_not_blocked(vm):
    vm.flag_carry = True
    vm.registers[2] = 4
    vm.registers[3] = 12
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 48
    assert not vm.flag_carry


def test_mul_produces_high_bits_when_sign_flag_is_on(vm):
    vm.flag_sign = True
    vm.registers[2] = 20000
    vm.registers[3] = 200
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 0b111101
    assert not vm.flag_sign
    # TODO: Find out how the carry and overflow flags should be set.


def test_mul_with_sign_flag_and_negative_result(vm):
    vm.flag_sign = True
    vm.registers[2] = 20000
    vm.registers[3] = to_u16(-200)
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 0b1111111111000010
    assert vm.flag_sign


def test_mul_with_sign_flag_zero_result(vm):
    vm.flag_sign = True
    vm.registers[2] = 47
    vm.registers[3] = 0
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_mul_ignores_sign_flag_when_carry_is_blocked(vm):
    vm.flag_sign = True
    vm.flag_carry_block = True
    vm.registers[2] = 20000
    vm.registers[3] = 200
    vm.exec_mul("R1", "R2", "R3")
    assert vm.registers[1] == 2304
    assert not vm.flag_sign
    assert vm.flag_carry


def test_mul_increments_pc(vm):
    vm.exec_mul("R1", "R2", "R3")
    assert vm.pc == 1


def test_mul_does_not_affect_R0(vm):
    vm.registers[1] = 4
    vm.registers[2] = 3
    vm.exec_mul("R0", "R1", "R2")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_and(vm):
    with patch("hera.vm.VirtualMachine.exec_and") as mock_exec_and:
        vm.exec_one(Op("AND", ["R1", "R2", "R3"]))
        assert mock_exec_and.call_count == 1
        assert mock_exec_and.call_args == (("R1", "R2", "R3"), {})


def test_and_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    vm.exec_and("R1", "R2", "R3")
    assert vm.registers[1] == 27


def test_and_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    vm.exec_and("R1", "R2", "R3")
    assert vm.registers[1] == 2


def test_and_increments_pc(vm):
    vm.exec_and("R0", "R1", "R2")
    assert vm.pc == 1


def test_and_big_numbers(vm):
    vm.registers[2] = 62434
    vm.registers[3] = 17589
    vm.exec_and("R1", "R2", "R3")
    assert vm.registers[1] == 16544


def test_and_sets_zero_flag(vm):
    vm.registers[2] = 82
    vm.registers[3] = 0
    vm.exec_and("R1", "R2", "R3")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_and_sets_sign_flag(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-37)
    vm.exec_and("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_and_does_not_set_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.exec_and("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_and_does_not_clear_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.exec_and("R1", "R2", "R3")
    assert vm.flag_carry
    assert vm.flag_overflow


def test_and_does_not_affect_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 1
    vm.exec_and("R0", "R1", "R2")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_or(vm):
    with patch("hera.vm.VirtualMachine.exec_or") as mock_exec_or:
        vm.exec_one(Op("OR", ["R1", "R2", "R3"]))
        assert mock_exec_or.call_count == 1
        assert mock_exec_or.call_args == (("R1", "R2", "R3"), {})


def test_or_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    vm.exec_or("R1", "R2", "R3")
    assert vm.registers[1] == 27


def test_or_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    vm.exec_or("R1", "R2", "R3")
    assert vm.registers[1] == 7


def test_or_increments_pc(vm):
    vm.exec_or("R0", "R1", "R2")
    assert vm.pc == 1


def test_or_big_numbers(vm):
    vm.registers[2] = 8199
    vm.registers[3] = 762
    vm.exec_or("R1", "R2", "R3")
    assert vm.registers[1] == 8959


def test_or_sets_zero_flag(vm):
    vm.registers[2] = 0
    vm.registers[3] = 0
    vm.exec_or("R1", "R2", "R3")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_or_sets_sign_flag(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-37)
    vm.exec_or("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_or_does_not_set_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.exec_or("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_or_does_not_clear_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.exec_or("R1", "R2", "R3")
    assert vm.flag_carry
    assert vm.flag_overflow


def test_or_does_not_affect_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 1
    vm.exec_or("R0", "R1", "R2")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_xor(vm):
    with patch("hera.vm.VirtualMachine.exec_xor") as mock_exec_xor:
        vm.exec_one(Op("XOR", ["R1", "R2", "R3"]))
        assert mock_exec_xor.call_count == 1
        assert mock_exec_xor.call_args == (("R1", "R2", "R3"), {})


def test_xor_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    vm.exec_xor("R1", "R2", "R3")
    assert vm.registers[1] == 0


def test_xor_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    vm.exec_xor("R1", "R2", "R3")
    assert vm.registers[1] == 5


def test_xor_increments_pc(vm):
    vm.exec_xor("R0", "R1", "R2")
    assert vm.pc == 1


def test_xor_big_numbers(vm):
    vm.registers[2] = 8199
    vm.registers[3] = 762
    vm.exec_xor("R1", "R2", "R3")
    assert vm.registers[1] == 8957


def test_xor_sets_zero_flag(vm):
    vm.registers[2] = 0
    vm.registers[3] = 0
    vm.exec_xor("R1", "R2", "R3")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_xor_sets_sign_flag(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)
    vm.exec_xor("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_xor_does_not_set_other_flags(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)
    vm.exec_xor("R1", "R2", "R3")
    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_xor_does_not_clear_other_flags(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.exec_xor("R1", "R2", "R3")
    assert vm.flag_carry
    assert vm.flag_overflow


def test_xor_does_not_affect_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 0
    vm.exec_xor("R0", "R1", "R2")
    assert vm.registers[0] == 0
