import pytest
from .utils import helper

from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_ADD_flags_and_pc(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = 1

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.pc == 1
    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_ADD_small_numbers(vm):
    vm.registers[2] = 20
    vm.registers[3] = 22

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.registers[1] == 42
    assert not vm.flag_overflow
    assert not vm.flag_carry


def test_ADD_resulting_in_negative(vm):
    vm.registers[2] = to_u16(-14)
    vm.registers[3] = 8

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-6)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_ADD_resulting_in_zero(vm):
    vm.registers[2] = to_u16(-4)
    vm.registers[3] = 4

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_ADD_resulting_in_overflow(vm):
    vm.registers[2] = 32767
    vm.registers[3] = 1

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-32768)
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_ADD_resulting_in_big_overflow(vm):
    vm.registers[2] = 32767
    vm.registers[3] = 32767

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-2)
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_ADD_resulting_in_negative_overflow(vm):
    vm.registers[2] = to_u16(-32768)
    vm.registers[3] = to_u16(-32768)

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.registers[1] == 0
    assert vm.flag_overflow
    assert vm.flag_carry


def test_ADD_with_carry_flag_set(vm):
    vm.flag_carry = True
    vm.registers[2] = 5
    vm.registers[3] = 3

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.registers[1] == 9
    assert not vm.flag_carry


def test_ADD_with_carry_and_block_flags_set(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.registers[2] = 5
    vm.registers[3] = 3

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.registers[1] == 8
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_ADD_with_overflow_from_carry(vm):
    vm.flag_carry = True
    vm.registers[2] = 32760
    vm.registers[3] = 7

    helper(vm, "ADD(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-32768)
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_SUB_flags_and_pc(vm):
    vm.flag_carry_block = True
    vm.registers[2] = 40
    vm.registers[3] = 100

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.pc == 1
    assert vm.registers[1] == to_u16(-60)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_SUB_small_numbers(vm):
    vm.flag_carry_block = True
    vm.registers[2] = 64
    vm.registers[3] = 22

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == 42
    assert not vm.flag_overflow
    assert vm.flag_carry


def test_SUB_resulting_in_negative(vm):
    vm.flag_carry_block = True
    vm.registers[2] = to_u16(-64)
    vm.registers[3] = 22

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-86)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_SUB_resulting_in_zero(vm):
    vm.flag_carry_block = True
    vm.registers[2] = to_u16(-37)
    vm.registers[3] = to_u16(-37)

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_SUB_with_two_negatives(vm):
    vm.flag_carry_block = True
    vm.registers[2] = to_u16(-20)
    vm.registers[3] = to_u16(-40)

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == 20
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_SUB_resulting_in_minimum_negative_overflow(vm):
    vm.flag_carry_block = True
    vm.registers[2] = to_u16(-32768)
    vm.registers[3] = 1

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == 32767
    assert vm.flag_carry
    assert vm.flag_overflow


def test_SUB_resulting_in_big_negative_overflow(vm):
    vm.flag_carry_block = True
    vm.registers[2] = to_u16(-32000)
    vm.registers[3] = 32000

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == 1536
    assert vm.flag_carry
    assert vm.flag_overflow


def test_SUB_resulting_in_maximum_negative_overflow(vm):
    vm.flag_carry_block = True
    vm.registers[2] = to_u16(-32768)
    vm.registers[3] = 32767

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == 1
    assert vm.flag_carry
    assert vm.flag_overflow


def test_SUB_resulting_in_minimum_positive_overflow(vm):
    vm.flag_carry_block = True
    vm.registers[2] = 32767
    vm.registers[3] = to_u16(-1)

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-32768)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_SUB_resulting_in_big_positive_overflow(vm):
    vm.flag_carry_block = True
    vm.registers[2] = 27500
    vm.registers[3] = to_u16(-7040)

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-30996)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_SUB_resulting_in_maximum_positive_overflow(vm):
    vm.flag_carry_block = True
    vm.registers[2] = 32767
    vm.registers[3] = to_u16(-32768)

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_SUB_with_implicit_borrow(vm):
    vm.registers[2] = 17
    vm.registers[3] = 5

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == 11


def test_SUB_with_no_carry_block_and_no_borrow(vm):
    vm.flag_carry = True
    vm.registers[2] = to_u16(-64)
    vm.registers[3] = 22

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-86)
    assert vm.flag_carry


def test_SUB_overflow_from_borrow(vm):
    vm.registers[2] = to_u16(-32767)
    vm.registers[3] = 1

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == 32767
    assert vm.flag_carry
    assert vm.flag_overflow


def test_SUB_overflow_takes_borrow_into_account(vm):
    vm.registers[2] = 10
    vm.registers[3] = 11

    helper(vm, "SUB(R1, R2, R3)")

    assert not vm.flag_overflow


def test_SUB_sets_carry_for_equal_operands(vm):
    vm.flag_carry = True
    vm.registers[2] = 12
    vm.registers[3] = 12

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == 0
    assert vm.flag_carry


def test_SUB_does_not_set_carry_for_equal_operands_with_no_incoming_carry(vm):
    vm.registers[2] = 12
    vm.registers[3] = 12

    helper(vm, "SUB(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry


def test_MUL_with_small_positives(vm):
    vm.registers[2] = 4
    vm.registers[3] = 2

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == 8


def test_MUL_with_large_positives(vm):
    vm.registers[2] = 4500
    vm.registers[3] = 3

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == 13500


def test_MUL_with_small_negatives(vm):
    vm.registers[2] = to_u16(-5)
    vm.registers[3] = 3

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-15)


def test_MUL_with_large_negatives(vm):
    vm.registers[2] = 7
    vm.registers[3] = to_u16(-3100)

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-21700)


def test_MUL_resulting_in_signed_positive_overflow(vm):
    vm.registers[2] = 17000
    vm.registers[3] = 3

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-14536)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_MUL_resulting_in_unsigned_positive_overflow(vm):
    vm.registers[2] = 128
    vm.registers[3] = 749

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == 30336
    assert vm.flag_carry
    assert vm.flag_overflow


def test_MUL_resulting_in_signed_negative_overflow(vm):
    vm.registers[2] = to_u16(-400)
    vm.registers[3] = to_u16(-200)

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == 14464
    assert vm.flag_carry
    assert vm.flag_overflow


def test_MUL_ignores_carry_when_blocked(vm):
    vm.flag_carry_block = True
    vm.flag_carry = True
    vm.registers[2] = 4
    vm.registers[3] = 12

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == 48
    assert not vm.flag_carry


def test_MUL_ignores_carry_when_not_blocked(vm):
    vm.flag_carry = True
    vm.registers[2] = 4
    vm.registers[3] = 12

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == 48
    assert not vm.flag_carry


def test_MUL_produces_high_bits_when_sign_flag_is_on(vm):
    vm.flag_sign = True
    vm.registers[2] = 20000
    vm.registers[3] = 200

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == 0b111101
    # TODO: Find out how the carry and overflow flags should be set.


def test_MUL_with_sign_flag_and_negative_result(vm):
    vm.flag_sign = True
    vm.registers[2] = 20000
    vm.registers[3] = to_u16(-200)

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == 0b1111111111000010


def test_MUL_ignores_sign_flag_when_carry_is_blocked(vm):
    vm.flag_sign = True
    vm.flag_carry_block = True
    vm.registers[2] = 20000
    vm.registers[3] = 200

    helper(vm, "MUL(R1, R2, R3)")

    assert vm.registers[1] == 2304
    assert vm.flag_carry


def test_AND_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27

    helper(vm, "AND(R1, R2, R3)")

    assert vm.registers[1] == 27


def test_AND_different_numbers(vm):
    vm.registers[2] = 0b011
    vm.registers[3] = 0b110

    helper(vm, "AND(R1, R2, R3)")

    assert vm.registers[1] == 0b010


def test_AND_big_numbers(vm):
    vm.registers[2] = 62434
    vm.registers[3] = 17589

    helper(vm, "AND(R1, R2, R3)")

    assert vm.registers[1] == 16544


def test_AND_does_not_set_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)

    helper(vm, "AND(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_AND_does_not_clear_other_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)

    helper(vm, "AND(R1, R2, R3)")

    assert vm.flag_carry
    assert vm.flag_overflow


def test_OR_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27

    helper(vm, "OR(R1, R2, R3)")

    assert vm.registers[1] == 27


def test_OR_different_numbers(vm):
    vm.registers[2] = 0b011
    vm.registers[3] = 0b110

    helper(vm, "OR(R1, R2, R3)")

    assert vm.registers[1] == 0b111


def test_OR_big_numbers(vm):
    vm.registers[2] = 8199
    vm.registers[3] = 762

    helper(vm, "OR(R1, R2, R3)")

    assert vm.registers[1] == 8959


def test_OR_does_not_set_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)

    helper(vm, "OR(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_OR_does_not_clear_other_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)

    helper(vm, "OR(R1, R2, R3)")

    assert vm.flag_carry
    assert vm.flag_overflow


def test_XOR_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27

    helper(vm, "XOR(R1, R2, R3)")

    assert vm.registers[1] == 0


def test_XOR_different_numbers(vm):
    vm.registers[2] = 0b011
    vm.registers[3] = 0b110

    helper(vm, "XOR(R1, R2, R3)")

    assert vm.registers[1] == 0b101


def test_XOR_big_numbers(vm):
    vm.registers[2] = 8199
    vm.registers[3] = 762

    helper(vm, "XOR(R1, R2, R3)")

    assert vm.registers[1] == 8957


def test_XOR_does_not_set_other_flags(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)

    helper(vm, "XOR(R1, R2, R3)")

    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_XOR_does_not_clear_other_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)

    helper(vm, "XOR(R1, R2, R3)")

    assert vm.flag_carry
    assert vm.flag_overflow
