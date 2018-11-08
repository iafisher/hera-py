import pytest
from unittest.mock import patch

from hera.parser import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_set(vm):
    with patch('hera.vm.VirtualMachine.exec_set') as mock_exec_set:
        vm.exec_one(Op('SET', ['R1', 47]))
        assert mock_exec_set.call_count == 1
        assert mock_exec_set.call_args == (('R1', 47), {})


def test_set_with_positive(vm):
    vm.exec_set('R1', 47)
    assert vm.registers[1] == 47


def test_set_with_negative(vm):
    vm.exec_set('R1', to_u16(-6453))
    assert vm.registers[1] == to_u16(-6453)


def test_set_increments_pc(vm):
    vm.exec_set('R1', 47)
    assert vm.pc == 1


def test_set_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False
    vm.exec_set('R7', 0)
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_set_does_not_set_zero_flag(vm):
    vm.exec_set('R7', 0)
    assert not vm.flag_zero


def test_set_does_not_set_sign_flag(vm):
    vm.exec_set('R7', to_u16(-1))
    assert not vm.flag_sign


def test_set_does_not_change_R0(vm):
    vm.exec_set('R0', 666)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_setlo(vm):
    with patch('hera.vm.VirtualMachine.exec_setlo') as mock_exec_setlo:
        vm.exec_one(Op('SETLO', ['R1', 47]))
        assert mock_exec_setlo.call_count == 1
        assert mock_exec_setlo.call_args == (('R1', 47), {})


def test_setlo_with_positive(vm):
    vm.exec_setlo('R5', 23)
    assert vm.registers[5] == 23


def test_setlo_with_negative(vm):
    vm.exec_setlo('R9', -12)
    assert vm.registers[9] == to_u16(-12)


def test_setlo_with_max_positive(vm):
    vm.exec_setlo('R2', 127)
    assert vm.registers[2] == 127


def test_setlo_with_max_negative(vm):
    vm.exec_setlo('R2', -128)
    assert vm.registers[2] == to_u16(-128)


def test_setlo_clears_high_bits(vm):
    vm.registers[6] = 4765
    vm.exec_setlo('R6', 68)
    assert vm.registers[6] == 68


def test_setlo_increments_pc(vm):
    vm.exec_setlo('R9', -12)
    assert vm.pc == 1


def test_setlo_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False
    vm.exec_setlo('R7', 0)
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_setlo_does_not_set_zero_flag(vm):
    vm.exec_setlo('R7', 0)
    assert not vm.flag_zero


def test_setlo_does_not_set_sign_flag(vm):
    vm.exec_setlo('R7', -1)
    assert not vm.flag_sign


def test_setlo_does_not_change_R0(vm):
    vm.exec_setlo('R0', 20)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_sethi(vm):
    with patch('hera.vm.VirtualMachine.exec_sethi') as mock_exec_sethi:
        vm.exec_one(Op('SETHI', ['R1', 47]))
        assert mock_exec_sethi.call_count == 1
        assert mock_exec_sethi.call_args == (('R1', 47), {})


def test_sethi_with_positive(vm):
    vm.exec_sethi('R5', 23)
    assert vm.registers[5] == 5888


def test_sethi_with_max_positive(vm):
    vm.exec_sethi('R2', 255)
    assert vm.registers[2] == 65280


def test_sethi_does_not_clear_low_bits(vm):
    vm.registers[6] = 4765
    vm.exec_sethi('R6', 68)
    assert vm.registers[6] == 17565


def test_sethi_increments_pc(vm):
    vm.exec_sethi('R9', 12)
    assert vm.pc == 1


def test_sethi_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False
    vm.exec_sethi('R7', 0)
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_sethi_does_not_set_zero_flag(vm):
    vm.exec_sethi('R7', 0)
    assert not vm.flag_zero


def test_sethi_does_not_set_sign_flag(vm):
    vm.exec_sethi('R7', -1)
    assert not vm.flag_sign


def test_sethi_does_not_change_R0(vm):
    vm.exec_sethi('R0', 20)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_add(vm):
    with patch('hera.vm.VirtualMachine.exec_add') as mock_exec_add:
        vm.exec_one(Op('ADD', ['R1', 'R2', 'R3']))
        assert mock_exec_add.call_count == 1
        assert mock_exec_add.call_args == (('R1', 'R2', 'R3'), {})


def test_add_small_numbers(vm):
    vm.registers[2] = 20
    vm.registers[3] = 22
    vm.exec_add('R1', 'R2', 'R3')
    assert vm.registers[1] == 42


def test_add_increments_pc(vm):
    vm.exec_add('R1', 'R2', 'R3')
    assert vm.pc == 1


def test_add_sets_flags(vm):
    vm.registers[2] = 20
    vm.registers[3] = 22
    vm.exec_add('R1', 'R2', 'R3')
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_negative(vm):
    vm.registers[2] = to_u16(-14)
    vm.registers[3] = 8
    vm.exec_add('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-6)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_add_with_zero(vm):
    vm.registers[7] = to_u16(-4)
    vm.registers[3] = 4
    vm.exec_add('R5', 'R7', 'R3')
    assert vm.registers[5] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_add_with_overflow(vm):
    vm.registers[9] = 32767
    vm.registers[2] = 1
    vm.exec_add('R7', 'R9', 'R2')
    assert vm.registers[7] == to_u16(-32768)
    assert vm.flag_sign
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_big_overflow(vm):
    vm.registers[9] = 32767
    vm.registers[2] = 32767
    vm.exec_add('R7', 'R9', 'R2')
    assert vm.registers[7] == to_u16(-2)
    assert vm.flag_sign
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_negative_overflow(vm):
    vm.registers[9] = to_u16(-32768)
    vm.registers[2] = to_u16(-32768)
    vm.exec_add('R7', 'R9', 'R2')
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry


def test_add_with_carry(vm):
    vm.registers[3] = 5
    vm.registers[5] = 3
    vm.flag_carry = True
    vm.exec_add('R7', 'R3', 'R5')
    assert vm.registers[7] == 9
    assert not vm.flag_carry


def test_add_with_carry_and_block(vm):
    vm.registers[3] = 5
    vm.registers[5] = 3
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_add('R7', 'R3', 'R5')
    assert vm.registers[7] == 8
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_add_with_overflow_from_carry(vm):
    vm.registers[2] = 32760
    vm.registers[3] = 7
    vm.flag_carry = True
    vm.exec_add('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-32768)
    assert vm.flag_sign
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_does_not_change_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 1
    vm.exec_add('R0', 'R1', 'R2')
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_sub(vm):
    with patch('hera.vm.VirtualMachine.exec_sub') as mock_exec_sub:
        vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
        assert mock_exec_sub.call_count == 1
        assert mock_exec_sub.call_args == (('R1', 'R2', 'R3'), {})


def test_sub_small_numbers(vm):
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.flag_carry_block = True
    vm.exec_sub('R1', 'R2', 'R3')
    assert vm.registers[1] == 42


def test_sub_sets_flags(vm):
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.flag_carry_block = True
    vm.exec_sub('R1', 'R2', 'R3')
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry


def test_sub_increments_pc(vm):
    vm.exec_sub('R1', 'R2', 'R3')
    assert vm.pc == 1


def test_sub_with_negative(vm):
    vm.registers[2] = to_u16(-64)
    vm.registers[3] = 22
    vm.flag_carry_block = True
    vm.exec_sub('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-86)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_sub_with_zero(vm):
    vm.registers[2] = to_u16(-37)
    vm.registers[3] = to_u16(-37)
    vm.flag_carry_block = True
    vm.exec_sub('R1', 'R2', 'R3')
    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_sub_with_two_negatives(vm):
    vm.registers[2] = to_u16(-20)
    vm.registers[3] = to_u16(-40)
    vm.flag_carry_block = True
    vm.exec_sub('R1', 'R2', 'R3')
    assert vm.registers[1] == 20
    assert not vm.flag_sign
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_sub_with_min_negative_overflow(vm):
    vm.registers[1] = to_u16(-32768)
    vm.registers[2] = 1
    vm.flag_carry_block = True
    vm.exec_sub('R3', 'R1', 'R2')
    assert vm.registers[3] == 32767
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_big_negative_overflow(vm):
    vm.registers[1] = to_u16(-32000)
    vm.registers[2] = 32000
    vm.flag_carry_block = True
    vm.exec_sub('R3', 'R1', 'R2')
    assert vm.registers[3] == 1536
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_max_negative_overflow(vm):
    vm.registers[1] = to_u16(-32768)
    vm.registers[2] = 32767
    vm.flag_carry_block = True
    vm.exec_sub('R3', 'R1', 'R2')
    assert vm.registers[3] == 1
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_min_positive_overflow(vm):
    vm.registers[4] = 32767
    vm.registers[5] = to_u16(-1)
    vm.flag_carry_block = True
    vm.exec_sub('R6', 'R4', 'R5')
    assert vm.registers[6] == to_u16(-32768)
    assert vm.flag_sign
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_big_positive_overflow(vm):
    vm.registers[4] = 27500
    vm.registers[5] = to_u16(-7040)
    vm.flag_carry_block = True
    vm.exec_sub('R6', 'R4', 'R5')
    assert vm.registers[6] == to_u16(-30996)
    assert vm.flag_sign
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_max_positive_overflow(vm):
    vm.registers[4] = 32767
    vm.registers[5] = to_u16(-32768)
    vm.flag_carry_block = True
    vm.exec_sub('R6', 'R4', 'R5')
    assert vm.registers[6] == to_u16(-1)
    assert vm.flag_sign
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_implicit_borrow(vm):
    vm.registers[2] = 17
    vm.registers[3] = 5
    vm.exec_sub('R1', 'R2', 'R3')
    assert vm.registers[1] == 11


def test_sub_with_no_carry_block_and_no_borrow(vm):
    vm.registers[2] = to_u16(-64)
    vm.registers[3] = 22
    vm.flag_carry = True
    vm.exec_sub('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-86)
    assert vm.flag_carry


def test_sub_overflow_from_borrow(vm):
    vm.registers[1] = to_u16(-32767)
    vm.registers[2] = 1
    vm.exec_sub('R3', 'R1', 'R2')
    assert vm.registers[3] == 32767
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_does_not_affect_R0(vm):
    vm.registers[1] = 4
    vm.registers[2] = 3
    vm.exec_sub('R0', 'R1', 'R2')
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_mul(vm):
    with patch('hera.vm.VirtualMachine.exec_mul') as mock_exec_mul:
        vm.exec_one(Op('MUL', ['R1', 'R2', 'R3']))
        assert mock_exec_mul.call_count == 1
        assert mock_exec_mul.call_args == (('R1', 'R2', 'R3'), {})


def test_mul_with_small_positives(vm):
    vm.registers[2] = 4
    vm.registers[3] = 2
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 8


def test_mul_with_large_positives(vm):
    vm.registers[2] = 4500
    vm.registers[3] = 3
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 13500


def test_mul_with_small_negatives(vm):
    vm.registers[2] = to_u16(-5)
    vm.registers[3] = 3
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-15)


def test_mul_with_large_negatives(vm):
    vm.registers[2] = 7
    vm.registers[3] = to_u16(-3100)
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-21700)


def test_mul_sets_zero_flag(vm):
    vm.registers[2] = 7
    vm.registers[3] = 0
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_mul_sets_sign_flag(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = 17
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-17)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_mul_with_signed_positive_overflow(vm):
    vm.registers[2] = 17000
    vm.registers[3] = 3
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-14536)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_mul_with_unsigned_positive_overflow(vm):
    vm.registers[2] = 128
    vm.registers[3] = 749
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 30336
    assert vm.flag_carry
    assert vm.flag_overflow


def test_mul_with_signed_negative_overflow(vm):
    vm.registers[2] = to_u16(-400)
    vm.registers[3] = to_u16(-200)
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 14464
    assert vm.flag_carry
    assert vm.flag_overflow


def test_mul_ignores_carry_when_blocked(vm):
    vm.flag_carry_block = True
    vm.flag_carry = True
    vm.registers[2] = 4
    vm.registers[3] = 12
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 48
    assert not vm.flag_carry


def test_mul_ignores_carry_when_not_blocked(vm):
    vm.flag_carry = True
    vm.registers[2] = 4
    vm.registers[3] = 12
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 48
    assert not vm.flag_carry


def test_mul_produces_high_bits_when_sign_flag_is_on(vm):
    vm.flag_sign = True
    vm.registers[2] = 20000
    vm.registers[3] = 200
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 0b111101
    assert not vm.flag_sign
    # TODO: Find out how the carry and overflow flags should be set.


def test_mul_with_sign_flag_and_negative_result(vm):
    vm.flag_sign = True
    vm.registers[2] = 20000
    vm.registers[3] = to_u16(-200)
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 0b1111111111000010
    assert vm.flag_sign


def test_mul_with_sign_flag_zero_result(vm):
    vm.flag_sign = True
    vm.registers[2] = 47
    vm.registers[3] = 0
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_mul_ignores_sign_flag_when_carry_is_blocked(vm):
    vm.flag_sign = True
    vm.flag_carry_block = True
    vm.registers[2] = 20000
    vm.registers[3] = 200
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.registers[1] == 2304
    assert not vm.flag_sign
    assert vm.flag_carry


def test_mul_increments_pc(vm):
    vm.exec_mul('R1', 'R2', 'R3')
    assert vm.pc == 1


def test_mul_does_not_affect_R0(vm):
    vm.registers[1] = 4
    vm.registers[2] = 3
    vm.exec_mul('R0', 'R1', 'R2')
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_and(vm):
    with patch('hera.vm.VirtualMachine.exec_and') as mock_exec_and:
        vm.exec_one(Op('AND', ['R1', 'R2', 'R3']))
        assert mock_exec_and.call_count == 1
        assert mock_exec_and.call_args == (('R1', 'R2', 'R3'), {})


def test_and_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    vm.exec_and('R1', 'R2', 'R3')
    assert vm.registers[1] == 27


def test_and_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    vm.exec_and('R1', 'R2', 'R3')
    assert vm.registers[1] == 2


def test_and_increments_pc(vm):
    vm.exec_and('R0', 'R1', 'R2')
    assert vm.pc == 1


def test_and_big_numbers(vm):
    vm.registers[2] = 62434
    vm.registers[3] = 17589
    vm.exec_and('R1', 'R2', 'R3')
    assert vm.registers[1] == 16544


def test_and_sets_zero_flag(vm):
    vm.registers[2] = 82
    vm.registers[3] = 0
    vm.exec_and('R1', 'R2', 'R3')
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_and_sets_sign_flag(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-37)
    vm.exec_and('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_and_does_not_set_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.exec_and('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_and_does_not_clear_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.exec_and('R1', 'R2', 'R3')
    assert vm.flag_carry
    assert vm.flag_overflow


def test_and_does_not_affect_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 1
    vm.exec_and('R0', 'R1', 'R2')
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_or(vm):
    with patch('hera.vm.VirtualMachine.exec_or') as mock_exec_or:
        vm.exec_one(Op('OR', ['R1', 'R2', 'R3']))
        assert mock_exec_or.call_count == 1
        assert mock_exec_or.call_args == (('R1', 'R2', 'R3'), {})


def test_or_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    vm.exec_or('R1', 'R2', 'R3')
    assert vm.registers[1] == 27


def test_or_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    vm.exec_or('R1', 'R2', 'R3')
    assert vm.registers[1] == 7


def test_or_increments_pc(vm):
    vm.exec_or('R0', 'R1', 'R2')
    assert vm.pc == 1


def test_or_big_numbers(vm):
    vm.registers[2] = 8199
    vm.registers[3] = 762
    vm.exec_or('R1', 'R2', 'R3')
    assert vm.registers[1] == 8959


def test_or_sets_zero_flag(vm):
    vm.registers[2] = 0
    vm.registers[3] = 0
    vm.exec_or('R1', 'R2', 'R3')
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_or_sets_sign_flag(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-37)
    vm.exec_or('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_or_does_not_set_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.exec_or('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_or_does_not_clear_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.exec_or('R1', 'R2', 'R3')
    assert vm.flag_carry
    assert vm.flag_overflow


def test_or_does_not_affect_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 1
    vm.exec_or('R0', 'R1', 'R2')
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_xor(vm):
    with patch('hera.vm.VirtualMachine.exec_xor') as mock_exec_xor:
        vm.exec_one(Op('XOR', ['R1', 'R2', 'R3']))
        assert mock_exec_xor.call_count == 1
        assert mock_exec_xor.call_args == (('R1', 'R2', 'R3'), {})


def test_xor_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    vm.exec_xor('R1', 'R2', 'R3')
    assert vm.registers[1] == 0


def test_xor_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    vm.exec_xor('R1', 'R2', 'R3')
    assert vm.registers[1] == 5


def test_xor_increments_pc(vm):
    vm.exec_xor('R0', 'R1', 'R2')
    assert vm.pc == 1


def test_xor_big_numbers(vm):
    vm.registers[2] = 8199
    vm.registers[3] = 762
    vm.exec_xor('R1', 'R2', 'R3')
    assert vm.registers[1] == 8957


def test_xor_sets_zero_flag(vm):
    vm.registers[2] = 0
    vm.registers[3] = 0
    vm.exec_xor('R1', 'R2', 'R3')
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_xor_sets_sign_flag(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)
    vm.exec_xor('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_xor_does_not_set_other_flags(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)
    vm.exec_xor('R1', 'R2', 'R3')
    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_xor_does_not_clear_other_flags(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.exec_xor('R1', 'R2', 'R3')
    assert vm.flag_carry
    assert vm.flag_overflow


def test_xor_does_not_affect_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 0
    vm.exec_xor('R0', 'R1', 'R2')
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_inc(vm):
    with patch('hera.vm.VirtualMachine.exec_inc') as mock_exec_inc:
        vm.exec_one(Op('INC', ['R1', 1]))
        assert mock_exec_inc.call_count == 1
        assert mock_exec_inc.call_args == (('R1', 1), {})


def test_inc_with_small_positive(vm):
    vm.exec_inc('R8', 6)
    assert vm.registers[8] == 6


def test_inc_with_max(vm):
    vm.exec_inc('R2', 32)
    assert vm.registers[2] == 32


def test_inc_with_previous_value(vm):
    vm.registers[5] = 4000
    vm.exec_inc('R5', 2)
    assert vm.registers[5] == 4002


def test_inc_with_previous_negative_value(vm):
    vm.registers[9] = to_u16(-12)
    vm.exec_inc('R9', 10)
    assert vm.registers[9] == to_u16(-2)


def test_inc_increments_pc(vm):
    vm.exec_inc('R1', 1)
    assert vm.pc == 1


def test_inc_sets_zero_flag(vm):
    vm.registers[7] = to_u16(-1)
    vm.exec_inc('R7', 1)
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_inc_sets_sign_flag(vm):
    vm.registers[1] = 32765
    vm.exec_inc('R1', 5)
    assert vm.registers[1] == to_u16(-32766)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_inc_sets_carry_flag(vm):
    vm.registers[8] = to_u16(-1)
    vm.exec_inc('R8', 1)
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_inc_sets_overflow_flag(vm):
    vm.registers[8] = 32765
    vm.exec_inc('R8', 5)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_inc_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.exec_inc('R8', 5)
    assert vm.registers[8] == 5
    assert not vm.flag_carry


def test_inc_does_not_affect_R0(vm):
    vm.exec_inc('R0', 1)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_dec(vm):
    with patch('hera.vm.VirtualMachine.exec_dec') as mock_exec_dec:
        vm.exec_one(Op('DEC', ['R1', 1]))
        assert mock_exec_dec.call_count == 1
        assert mock_exec_dec.call_args == (('R1', 1), {})


def test_dec_with_small_positive(vm):
    vm.exec_dec('R8', 6)
    assert vm.registers[8] == to_u16(-6)


def test_dec_with_max(vm):
    vm.exec_dec('R2', 32)
    assert vm.registers[2] == to_u16(-32)


def test_dec_with_previous_value(vm):
    vm.registers[5] = 4000
    vm.exec_dec('R5', 2)
    assert vm.registers[5] == 3998


def test_dec_with_previous_negative_value(vm):
    vm.registers[9] = to_u16(-12)
    vm.exec_dec('R9', 10)
    assert vm.registers[9] == to_u16(-22)


def test_dec_increments_pc(vm):
    vm.exec_dec('R1', 1)
    assert vm.pc == 1


def test_dec_sets_zero_flag(vm):
    vm.registers[7] = 1
    vm.exec_dec('R7', 1)
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_dec_sets_sign_flag(vm):
    vm.registers[1] = 1
    vm.exec_dec('R1', 5)
    assert vm.registers[1] == to_u16(-4)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_dec_sets_carry_flag(vm):
    vm.exec_dec('R8', 1)
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_dec_sets_overflow_flag(vm):
    vm.registers[8] = to_u16(-32768)
    vm.exec_dec('R8', 5)
    assert vm.registers[8] == 32763
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_dec_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[8] = 10
    vm.exec_dec('R8', 5)
    assert vm.registers[8] == 5
    assert not vm.flag_carry


def test_dec_does_not_affect_R0(vm):
    vm.exec_dec('R0', 1)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_lsl(vm):
    with patch('hera.vm.VirtualMachine.exec_lsl') as mock_exec_lsl:
        vm.exec_one(Op('LSL', ['R1', 'R2']))
        assert mock_exec_lsl.call_count == 1
        assert mock_exec_lsl.call_args == (('R1', 'R2'), {})


def test_lsl_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == 14


def test_lsl_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == 30000


def test_lsl_with_positive_overflow(vm):
    vm.registers[6] = 17000
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == 34000


def test_lsl_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == to_u16(-14)


def test_lsl_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == to_u16(-16800)


def test_lsl_with_negative_overflow(vm):
    vm.registers[6] = to_u16(-20000)
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == 25536
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_lsl_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = to_u16(-20000)
    vm.flag_carry_block = True
    vm.exec_lsl('R1', 'R6')
    assert vm.flag_carry


def test_lsl_shifts_in_carry(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == 15
    assert not vm.flag_carry


def test_lsl_ignores_carry_when_blocked(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == 14
    assert not vm.flag_carry


def test_lsl_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_lsl('R6', 'R6')
    assert not vm.flag_carry


def test_lsl_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_lsl('R0', 'R6')
    assert vm.registers[0] == 0


def test_lsl_increments_pc(vm):
    vm.exec_lsl('R6', 'R6')
    assert vm.pc == 1


def test_lsl_sets_zero_flag(vm):
    vm.registers[6] = 32768
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_lsl_sets_sign_flag(vm):
    vm.registers[6] = 32767
    vm.exec_lsl('R1', 'R6')
    assert vm.registers[1] == to_u16(-2)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_lsl_ignores_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_lsl('R1', 'R6')
    assert vm.flag_overflow


def test_exec_one_delegates_to_lsr(vm):
    with patch('hera.vm.VirtualMachine.exec_lsr') as mock_exec_lsr:
        vm.exec_one(Op('LSR', ['R1', 'R2']))
        assert mock_exec_lsr.call_count == 1
        assert mock_exec_lsr.call_args == (('R1', 'R2'), {})


def test_lsr_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_lsr('R1', 'R6')
    assert vm.registers[1] == 3


def test_lsr_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_lsr('R1', 'R6')
    assert vm.registers[1] == 7500


def test_lsr_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_lsr('R1', 'R6')
    assert vm.registers[1] == 32764


def test_lsr_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_lsr('R1', 'R6')
    assert vm.registers[1] == 28568


def test_lsr_with_another_large_nevative(vm):
    vm.registers[6] = to_u16(-20000)
    vm.exec_lsr('R1', 'R6')
    assert vm.registers[1] == 22768


def test_lsr_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = 3
    vm.flag_carry_block = True
    vm.exec_lsr('R1', 'R6')
    assert vm.registers[1] == 1
    assert vm.flag_carry


def test_lsr_shifts_in_carry(vm):
    vm.registers[6] = 6
    vm.flag_carry = True
    vm.exec_lsr('R1', 'R6')
    assert vm.registers[1] == to_u16(-32765)
    assert not vm.flag_carry


def test_lsr_ignores_carry_when_blocked(vm):
    vm.registers[6] = 6
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_lsr('R1', 'R6')
    assert vm.registers[1] == 3
    assert not vm.flag_carry


def test_lsr_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_lsr('R6', 'R6')
    assert not vm.flag_carry


def test_lsr_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_lsr('R0', 'R6')
    assert vm.registers[0] == 0


def test_lsr_increments_pc(vm):
    vm.exec_lsr('R6', 'R6')
    assert vm.pc == 1


def test_lsr_sets_zero_flag(vm):
    vm.registers[6] = 1
    vm.exec_lsr('R1', 'R6')
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_lsr_sets_sign_flag(vm):
    vm.registers[6] = 6
    vm.flag_carry = True
    vm.exec_lsr('R1', 'R6')
    assert not vm.flag_zero
    assert vm.flag_sign


def test_lsr_ignores_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_lsr('R1', 'R6')
    assert vm.flag_overflow


def test_exec_one_delegates_to_lsl8(vm):
    with patch('hera.vm.VirtualMachine.exec_lsl8') as mock_exec_lsl8:
        vm.exec_one(Op('LSL8', ['R1', 'R2']))
        assert mock_exec_lsl8.call_count == 1
        assert mock_exec_lsl8.call_args == (('R1', 'R2'), {})


def test_lsl8_with_small_positive(vm):
    vm.registers[4] = 51
    vm.exec_lsl8('R3', 'R4')
    assert vm.registers[3] == 13056


def test_lsl8_with_large_positive(vm):
    vm.registers[4] = 17000
    vm.exec_lsl8('R3', 'R4')
    assert vm.registers[3] == 26624


def test_lsl8_with_small_negative(vm):
    vm.registers[4] = -4
    vm.exec_lsl8('R3', 'R4')
    assert vm.registers[3] == to_u16(-1024)


def test_lsl8_with_large_negative(vm):
    vm.registers[4] = to_u16(-31781)
    vm.exec_lsl8('R3', 'R4')
    assert vm.registers[3] == to_u16(-9472)


def test_lsl8_sets_zero_flag(vm):
    vm.registers[4] = 32768
    vm.exec_lsl8('R3', 'R4')
    assert vm.registers[3] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_lsl8_sets_sign_flag(vm):
    vm.registers[4] = 32767
    vm.exec_lsl8('R3', 'R4')
    assert vm.registers[3] == to_u16(-256)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_lsl8_increments_pc(vm):
    vm.exec_lsl8('R1', 'R1')
    assert vm.pc == 1


def test_lsl8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[4] = 5
    vm.exec_lsl8('R3', 'R4')
    assert vm.registers[3] == 1280
    assert vm.flag_carry


def test_lsl8_does_not_set_carry_or_overflow(vm):
    vm.registers[4] = to_u16(-1)
    vm.exec_lsl8('R3', 'R4')
    assert vm.registers[3] == to_u16(-256)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_lsl8_does_not_affect_R0(vm):
    vm.registers[4] = 4
    vm.exec_lsl8('R0', 'R4')
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_lsr8(vm):
    with patch('hera.vm.VirtualMachine.exec_lsr8') as mock_exec_lsr8:
        vm.exec_one(Op('LSR8', ['R1', 'R2']))
        assert mock_exec_lsr8.call_count == 1
        assert mock_exec_lsr8.call_args == (('R1', 'R2'), {})


def test_lsr8_with_small_positive(vm):
    vm.registers[4] = 51
    vm.exec_lsr8('R3', 'R4')
    assert vm.registers[3] == 0


def test_lsr8_with_large_positive(vm):
    vm.registers[4] = 17000
    vm.exec_lsr8('R3', 'R4')
    assert vm.registers[3] == 66


def test_lsr8_with_small_negative(vm):
    vm.registers[4] = to_u16(-4)
    vm.exec_lsr8('R3', 'R4')
    assert vm.registers[3] == 255


def test_lsr8_with_large_negative(vm):
    vm.registers[4] = to_u16(-31781)
    vm.exec_lsr8('R3', 'R4')
    assert vm.registers[3] == 131


def test_lsr8_sets_zero_flag(vm):
    vm.registers[4] = 17
    vm.exec_lsr8('R3', 'R4')
    assert vm.registers[3] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_lsr8_increments_pc(vm):
    vm.exec_lsr8('R1', 'R1')
    assert vm.pc == 1


def test_lsr8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[4] = 17000
    vm.exec_lsr8('R3', 'R4')
    assert vm.registers[3] == 66
    assert vm.flag_carry


def test_lsr8_does_not_set_carry_or_overflow(vm):
    vm.registers[4] = 15910
    vm.exec_lsr8('R3', 'R4')
    assert vm.registers[3] == 62
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_lsr8_does_not_affect_R0(vm):
    vm.registers[4] = 15910
    vm.exec_lsr8('R0', 'R4')
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_asl(vm):
    with patch('hera.vm.VirtualMachine.exec_asl') as mock_exec_asl:
        vm.exec_one(Op('ASL', ['R1', 'R2']))
        assert mock_exec_asl.call_count == 1
        assert mock_exec_asl.call_args == (('R1', 'R2'), {})


def test_asl_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == 14


def test_asl_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == 30000


def test_asl_with_positive_overflow(vm):
    vm.registers[6] = 17000
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == 34000


def test_asl_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == to_u16(-14)


def test_asl_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == to_u16(-16800)


def test_asl_with_negative_overflow(vm):
    vm.registers[6] = to_u16(-20000)
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == 25536
    assert vm.flag_carry
    assert vm.flag_overflow


def test_asl_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = to_u16(-20000)
    vm.flag_carry_block = True
    vm.exec_asl('R1', 'R6')
    assert vm.flag_carry
    assert vm.flag_overflow


def test_asl_shifts_in_carry(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == 15
    assert not vm.flag_carry


def test_asl_ignores_carry_when_blocked(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == 14
    assert not vm.flag_carry


def test_asl_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_asl('R6', 'R6')
    assert not vm.flag_carry


def test_asl_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_asl('R0', 'R6')
    assert vm.registers[0] == 0


def test_asl_increments_pc(vm):
    vm.exec_asl('R6', 'R6')
    assert vm.pc == 1


def test_asl_sets_zero_flag(vm):
    vm.registers[6] = 32768
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_asl_sets_sign_flag(vm):
    vm.registers[6] = 32767
    vm.exec_asl('R1', 'R6')
    assert vm.registers[1] == to_u16(-2)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_asl_resets_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_asl('R1', 'R6')
    assert not vm.flag_overflow


def test_exec_one_delegates_to_asr(vm):
    with patch('hera.vm.VirtualMachine.exec_asr') as mock_exec_asr:
        vm.exec_one(Op('ASR', ['R1', 'R2']))
        assert mock_exec_asr.call_count == 1
        assert mock_exec_asr.call_args == (('R1', 'R2'), {})


def test_asr_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_asr('R1', 'R6')
    assert vm.registers[1] == 3


def test_asr_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_asr('R1', 'R6')
    assert vm.registers[1] == 7500


def test_asr_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_asr('R1', 'R6')
    assert vm.registers[1] == to_u16(-3)


def test_asr_with_another_small_negative(vm):
    vm.registers[6] = to_u16(-5)
    vm.exec_asr('R1', 'R6')
    assert vm.registers[1] == to_u16(-2)


def test_asr_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_asr('R1', 'R6')
    assert vm.registers[1] == to_u16(-4200)


def test_asr_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = 3
    vm.flag_carry_block = True
    vm.exec_asr('R1', 'R6')
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_asr_ignores_incoming_carry(vm):
    vm.registers[6] = 4
    vm.flag_carry = True
    vm.exec_asr('R1', 'R6')
    assert vm.registers[1] == 2
    assert not vm.flag_carry


def test_asr_ignores_carry_when_blocked(vm):
    vm.registers[6] = 4
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_asr('R1', 'R6')
    assert vm.registers[1] == 2
    assert not vm.flag_carry


def test_asr_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_asr('R6', 'R6')
    assert not vm.flag_carry


def test_asr_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_asr('R0', 'R6')
    assert vm.registers[0] == 0


def test_asr_increments_pc(vm):
    vm.exec_asr('R6', 'R6')
    assert vm.pc == 1


def test_asr_sets_zero_flag(vm):
    vm.registers[6] = 1
    vm.exec_asr('R1', 'R6')
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_asr_sets_sign_flag(vm):
    vm.registers[6] = to_u16(-20)
    vm.exec_asr('R1', 'R6')
    assert vm.registers[1] == to_u16(-10)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_asr_does_not_reset_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_asr('R1', 'R6')
    assert vm.flag_overflow


def test_exec_one_delegates_to_savef(vm):
    with patch('hera.vm.VirtualMachine.exec_savef') as mock_exec_savef:
        vm.exec_one(Op('SAVEF', ['R1']))
        assert mock_exec_savef.call_count == 1
        assert mock_exec_savef.call_args == (('R1',), {})


def test_savef_with_sign(vm):
    vm.flag_sign = True
    vm.exec_savef('R5')
    assert vm.registers[5] == 1
    assert vm.flag_sign


def test_savef_with_zero(vm):
    vm.flag_zero = True
    vm.exec_savef('R5')
    assert vm.registers[5] == 0b10
    assert vm.flag_zero


def test_savef_with_overflow(vm):
    vm.flag_overflow = True
    vm.exec_savef('R5')
    assert vm.registers[5] == 0b100
    assert vm.flag_overflow


def test_savef_with_carry(vm):
    vm.flag_carry = True
    vm.exec_savef('R5')
    assert vm.registers[5] == 0b1000
    assert vm.flag_carry


def test_savef_with_carry_block(vm):
    vm.flag_carry_block = True
    vm.exec_savef('R5')
    assert vm.registers[5] == 0b10000


def test_savef_with_several_flags(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.exec_savef('R5')
    assert vm.registers[5] == 0b1101
    assert vm.flag_sign
    assert vm.flag_overflow
    assert vm.flag_carry


def test_savef_with_all_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_savef('R5')
    assert vm.registers[5] == 0b11111
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_savef_with_no_flags(vm):
    vm.exec_savef('R5')
    assert vm.registers[5] == 0


def test_savef_overwrites_high_bits(vm):
    vm.registers[5] = 17500
    vm.exec_savef('R5')
    assert vm.registers[5] == 0


def test_savef_increments_pc(vm):
    vm.exec_savef('R5')
    assert vm.pc == 1


def test_savef_does_not_affect_R0(vm):
    vm.flag_carry = True
    vm.exec_savef('R0')
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_rstrf(vm):
    with patch('hera.vm.VirtualMachine.exec_rstrf') as mock_exec_rstrf:
        vm.exec_one(Op('RSTRF', ['R1']))
        assert mock_exec_rstrf.call_count == 1
        assert mock_exec_rstrf.call_args == (('R1',), {})


def test_rstrf_with_sign(vm):
    vm.registers[5] = 1
    vm.exec_rstrf('R5')
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_zero(vm):
    vm.registers[5] = 0b10
    vm.exec_rstrf('R5')
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_overflow(vm):
    vm.registers[5] = 0b100
    vm.exec_rstrf('R5')
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_carry(vm):
    vm.registers[5] = 0b1000
    vm.exec_rstrf('R5')
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_carry_block(vm):
    vm.registers[5] = 0b10000
    vm.exec_rstrf('R5')
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_rstrf_with_several_flags(vm):
    vm.registers[5] = 0b1101
    vm.exec_rstrf('R5')
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_all_flags(vm):
    vm.registers[5] = 0b11111
    vm.exec_rstrf('R5')
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_rstrf_with_no_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_rstrf('R5')
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_increments_pc(vm):
    vm.exec_rstrf('R5')
    assert vm.pc == 1


def test_exec_one_delegates_to_fon(vm):
    with patch('hera.vm.VirtualMachine.exec_fon') as mock_exec_fon:
        vm.exec_one(Op('FON', [5]))
        assert mock_exec_fon.call_count == 1
        assert mock_exec_fon.call_args == ((5,), {})


def test_fon_with_sign(vm):
    vm.exec_fon(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_with_zero(vm):
    vm.exec_fon(0b10)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_with_overflow(vm):
    vm.exec_fon(0b100)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_with_carry(vm):
    vm.exec_fon(0b1000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_with_carry_block(vm):
    vm.exec_fon(0b10000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_fon_with_multiple_flags(vm):
    vm.exec_fon(0b10101)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_fon_with_no_flags(vm):
    vm.exec_fon(0)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_does_not_overwrite_flags(vm):
    vm.flag_carry_block = True
    vm.exec_fon(1)
    assert vm.flag_sign
    assert vm.flag_carry_block


def test_fon_increments_pc(vm):
    vm.exec_fon(0)
    assert vm.pc == 1


def test_exec_one_delegates_to_foff(vm):
    with patch('hera.vm.VirtualMachine.exec_foff') as mock_exec_foff:
        vm.exec_one(Op('FOFF', [5]))
        assert mock_exec_foff.call_count == 1
        assert mock_exec_foff.call_args == ((5,), {})


def test_foff_with_sign(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(1)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_foff_with_zero(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b10)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_foff_with_overflow(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b100)
    assert vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_foff_with_carry(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b1000)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_foff_with_carry_block(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b10000)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_foff_with_multiple_flags(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b10101)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_foff_with_no_flags(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_foff_increments_pc(vm):
    vm.exec_foff(0)
    assert vm.pc == 1


def test_exec_one_delegates_to_fset5(vm):
    with patch('hera.vm.VirtualMachine.exec_fset5') as mock_exec_fset5:
        vm.exec_one(Op('FSET5', [5]))
        assert mock_exec_fset5.call_count == 1
        assert mock_exec_fset5.call_args == ((5,), {})


def test_fset5_with_sign(vm):
    vm.exec_fset5(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_with_zero(vm):
    vm.exec_fset5(0b10)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_with_overflow(vm):
    vm.exec_fset5(0b100)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_with_carry(vm):
    vm.exec_fset5(0b1000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_with_carry_block(vm):
    vm.exec_fset5(0b10000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_fset5_with_multiple_flags(vm):
    vm.exec_fset5(0b10101)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_fset5_with_no_flags(vm):
    vm.exec_fset5(0)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_does_overwrite_flags(vm):
    vm.flag_zero = True
    vm.flag_carry_block = True
    vm.exec_fset5(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_carry_block


def test_fset5_increments_pc(vm):
    vm.exec_fset5(0)
    assert vm.pc == 1


def test_exec_one_delegates_to_fset4(vm):
    with patch('hera.vm.VirtualMachine.exec_fset4') as mock_exec_fset4:
        vm.exec_one(Op('FSET4', [5]))
        assert mock_exec_fset4.call_count == 1
        assert mock_exec_fset4.call_args == ((5,), {})


def test_fset4_with_sign(vm):
    vm.exec_fset4(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_zero(vm):
    vm.exec_fset4(0b10)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_overflow(vm):
    vm.exec_fset4(0b100)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_carry(vm):
    vm.exec_fset4(0b1000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_multiple_flags(vm):
    vm.exec_fset4(0b101)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_no_flags(vm):
    vm.exec_fset4(0)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_does_overwrite_flags(vm):
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.exec_fset4(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow


def test_fset4_increments_pc(vm):
    vm.exec_fset4(0)
    assert vm.pc == 1


def test_exec_one_delegates_to_load(vm):
    with patch('hera.vm.VirtualMachine.exec_load') as mock_exec_load:
        vm.exec_one(Op('LOAD', ['R1', 0, 'R2']))
        assert mock_exec_load.call_count == 1
        assert mock_exec_load.call_args == (('R1', 0, 'R2'), {})


def test_load_from_small_address(vm):
    vm.memory[3] = 42
    vm.registers[2] = 3
    vm.exec_load('R1', 0, 'R2')
    assert vm.registers[1] == 42


def test_load_from_uninitialized_address(vm):
    vm.registers[2] = 5
    vm.exec_load('R1', 0, 'R2')
    assert vm.registers[1] == 0


def test_load_from_large_uninitialized_address(vm):
    vm.registers[2] = 14000
    vm.exec_load('R1', 0, 'R2')
    assert vm.registers[1] == 0


def test_load_from_address_zero(vm):
    vm.memory[0] = 42
    vm.exec_load('R1', 0, 'R0')
    assert vm.registers[1] == 42


def test_load_with_offset(vm):
    vm.memory[7] = 42
    vm.registers[2] = 4
    vm.exec_load('R1', 3, 'R2')
    assert vm.registers[1] == 42


def test_load_sets_zero_flag(vm):
    vm.exec_load('R1', 0, 'R0')
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_load_sets_sign_flag(vm):
    vm.memory[4] = to_u16(-2)
    vm.registers[2] = 4
    vm.exec_load('R1', 0, 'R2')
    assert vm.registers[1] == to_u16(-2)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_load_ignores_other_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_carry_block = True
    vm.exec_load('R1', 0, 'R0')
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_carry_block


def test_load_does_not_affect_R0(vm):
    vm.memory[2] = 5
    vm.registers[2] = 2
    vm.exec_load('R0', 0, 'R2')
    assert vm.registers[0] == 0


def test_load_increments_pc(vm):
    vm.exec_load('R1', 0, 'R2')
    assert vm.pc == 1


def test_exec_one_delegates_to_store(vm):
    with patch('hera.vm.VirtualMachine.exec_store') as mock_exec_store:
        vm.exec_one(Op('STORE', ['R1', 0, 'R2']))
        assert mock_exec_store.call_count == 1
        assert mock_exec_store.call_args == (('R1', 0, 'R2'), {})


def test_store_to_small_address(vm):
    vm.registers[1] = 42
    vm.registers[2] = 3
    vm.exec_store('R1', 0, 'R2')
    assert vm.memory[3] == 42


def test_store_to_large_address(vm):
    vm.registers[1] = 42
    vm.registers[2] = 5000
    vm.exec_store('R1', 0, 'R2')
    assert vm.memory[5000] == 42


def test_store_to_max_address(vm):
    vm.registers[1] = 42
    vm.registers[2] = (2**16)-1
    vm.exec_store('R1', 0, 'R2')
    assert vm.memory[(2**16)-1] == 42


def test_store_to_address_zero(vm):
    vm.registers[1] = 42
    vm.exec_store('R1', 0, 'R0')
    assert vm.memory[0] == 42


def test_store_with_offset(vm):
    vm.registers[1] = 42
    vm.registers[2] = 4
    vm.exec_store('R1', 3, 'R2')
    assert vm.memory[7] == 42


def test_store_ignores_all_flags(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_carry_block = True
    vm.registers[1] = 42
    vm.exec_store('R1', 0, 'R0')
    assert vm.flag_zero
    assert vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_carry_block


def test_store_increments_pc(vm):
    vm.exec_store('R1', 0, 'R2')
    assert vm.pc == 1


def test_exec_one_delegates_to_br(vm):
    with patch('hera.vm.VirtualMachine.exec_br') as mock_exec_br:
        vm.exec_one(Op('BR', ['R1']))
        assert mock_exec_br.call_count == 1
        assert mock_exec_br.call_args == (('R1',), {})


def test_br_sets_pc(vm):
    vm.registers[7] = 170
    vm.exec_br('R7')
    assert vm.pc == 170


def test_br_sets_pc_to_zero(vm):
    vm.exec_br('R0')
    assert vm.pc == 0


def test_br_does_not_change_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.registers[7] = 92
    vm.exec_br('R7')
    assert vm.pc == 92
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_brr(vm):
    with patch('hera.vm.VirtualMachine.exec_brr') as mock_exec_brr:
        vm.exec_one(Op('BRR', [12]))
        assert mock_exec_brr.call_count == 1
        assert mock_exec_brr.call_args == ((12,), {})


def test_brr_sets_pc(vm):
    vm.exec_brr(100)
    assert vm.pc == 100


def test_brr_with_negative_offset(vm):
    vm.pc = 50
    vm.exec_brr(-17)
    assert vm.pc == 33


def test_brr_sets_pc_with_previous_value(vm):
    vm.pc = 100
    vm.exec_brr(15)
    assert vm.pc == 115


def test_brr_sets_pc_to_zero(vm):
    vm.exec_brr(0)
    assert vm.pc == 0


def test_brr_does_not_change_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_brr(16)
    assert vm.pc == 16
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block
