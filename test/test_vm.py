import pytest

from hera.parser import Op
from hera.utils import to_uint
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_add_small_numbers(vm):
    vm.registers[2] = 20
    vm.registers[3] = 22
    vm.exec_one(Op('ADD', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 42


def test_add_increments_pc(vm):
    vm.exec_one(Op('ADD', ['R1', 'R2', 'R3']))
    assert vm.pc == 1


def test_add_sets_flags(vm):
    vm.registers[2] = 20
    vm.registers[3] = 22
    vm.exec_one(Op('ADD', ['R1', 'R2', 'R3']))
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_negative(vm):
    vm.registers[2] = to_uint(-14)
    vm.registers[3] = 8
    vm.exec_one(Op('ADD', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == to_uint(-6)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_add_with_zero(vm):
    vm.registers[7] = to_uint(-4)
    vm.registers[3] = 4
    vm.exec_one(Op('ADD', ['R5', 'R7', 'R3']))
    assert vm.registers[5] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_add_with_overflow(vm):
    vm.registers[9] = 32767
    vm.registers[2] = 1
    vm.exec_one(Op('ADD', ['R7', 'R9', 'R2']))
    assert vm.registers[7] == to_uint(-32768)
    assert vm.flag_sign
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_big_overflow(vm):
    vm.registers[9] = 32767
    vm.registers[2] = 32767
    vm.exec_one(Op('ADD', ['R7', 'R9', 'R2']))
    assert vm.registers[7] == to_uint(-2)
    assert vm.flag_sign
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_negative_overflow(vm):
    vm.registers[9] = to_uint(-32768)
    vm.registers[2] = to_uint(-32768)
    vm.exec_one(Op('ADD', ['R7', 'R9', 'R2']))
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry


def test_add_with_carry(vm):
    vm.registers[3] = 5
    vm.registers[5] = 3
    vm.flag_carry = True
    vm.exec_one(Op('ADD', ['R7', 'R3', 'R5']))
    assert vm.registers[7] == 9
    assert not vm.flag_carry


def test_add_with_carry_and_block(vm):
    vm.registers[3] = 5
    vm.registers[5] = 3
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_one(Op('ADD', ['R7', 'R3', 'R5']))
    assert vm.registers[7] == 8
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_add_with_overflow_from_carry(vm):
    vm.registers[2] = 32760
    vm.registers[3] = 7
    vm.flag_carry = True
    vm.exec_one(Op('ADD', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == to_uint(-32768)
    assert vm.flag_sign
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_sub_small_numbers(vm):
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 42


def test_sub_sets_flags(vm):
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry


def test_sub_increments_pc(vm):
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.pc == 1


def test_sub_with_negative(vm):
    vm.registers[2] = to_uint(-64)
    vm.registers[3] = 22
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == to_uint(-86)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_sub_with_zero(vm):
    vm.registers[2] = to_uint(-37)
    vm.registers[3] = to_uint(-37)
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_sub_with_two_negatives(vm):
    vm.registers[2] = to_uint(-20)
    vm.registers[3] = to_uint(-40)
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 20
    assert not vm.flag_sign
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_sub_with_min_negative_overflow(vm):
    vm.registers[1] = to_uint(-32768)
    vm.registers[2] = 1
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R3', 'R1', 'R2']))
    assert vm.registers[3] == 32767
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_big_negative_overflow(vm):
    vm.registers[1] = to_uint(-32000)
    vm.registers[2] = 32000
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R3', 'R1', 'R2']))
    assert vm.registers[3] == 1536
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_max_negative_overflow(vm):
    vm.registers[1] = to_uint(-32768)
    vm.registers[2] = 32767
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R3', 'R1', 'R2']))
    assert vm.registers[3] == 1
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_min_positive_overflow(vm):
    vm.registers[4] = 32767
    vm.registers[5] = to_uint(-1)
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R6', 'R4', 'R5']))
    assert vm.registers[6] == to_uint(-32768)
    assert vm.flag_sign
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_big_positive_overflow(vm):
    vm.registers[4] = 27500
    vm.registers[5] = to_uint(-7040)
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R6', 'R4', 'R5']))
    assert vm.registers[6] == to_uint(-30996)
    assert vm.flag_sign
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_max_positive_overflow(vm):
    vm.registers[4] = 32767
    vm.registers[5] = to_uint(-32768)
    vm.flag_carry_block = True
    vm.exec_one(Op('SUB', ['R6', 'R4', 'R5']))
    assert vm.registers[6] == to_uint(-1)
    assert vm.flag_sign
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_sub_with_implicit_borrow(vm):
    vm.registers[2] = 17
    vm.registers[3] = 5
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 11


def test_sub_with_no_carry_block_and_no_borrow(vm):
    vm.registers[2] = to_uint(-64)
    vm.registers[3] = 22
    vm.flag_carry = True
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == to_uint(-86)
    assert vm.flag_carry  # TODO: Check this against HERA-C.


def test_sub_overflow_from_borrow(vm):
    vm.registers[1] = to_uint(-32767)
    vm.registers[2] = 1
    vm.exec_one(Op('SUB', ['R3', 'R1', 'R2']))
    assert vm.registers[3] == 32767
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow


def test_and_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    vm.exec_one(Op('AND', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 27


def test_and_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    vm.exec_one(Op('AND', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 2


def test_and_increments_pc(vm):
    vm.exec_one(Op('AND', ['R0', 'R1', 'R2']))
    assert vm.pc == 1


def test_and_big_numbers(vm):
    vm.registers[2] = 62434
    vm.registers[3] = 17589
    vm.exec_one(Op('AND', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 16544


def test_and_sets_zero_flag(vm):
    vm.registers[2] = 82
    vm.registers[3] = 0
    vm.exec_one(Op('AND', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_and_sets_sign_flag(vm):
    vm.registers[2] = to_uint(-1)
    vm.registers[3] = to_uint(-37)
    vm.exec_one(Op('AND', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == to_uint(-37)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_and_does_not_set_other_flags(vm):
    vm.registers[2] = to_uint(-1)
    vm.registers[3] = to_uint(-1)
    vm.exec_one(Op('AND', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == to_uint(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_and_does_not_clear_other_flags(vm):
    vm.registers[2] = to_uint(-1)
    vm.registers[3] = to_uint(-1)
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.exec_one(Op('AND', ['R1', 'R2', 'R3']))
    assert vm.flag_carry
    assert vm.flag_overflow
