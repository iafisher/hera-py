import pytest

from hera.parser import Op
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
    vm.registers[2] = -14
    vm.registers[3] = 8
    vm.exec_one(Op('ADD', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == -6
    assert vm.flag_sign
    assert not vm.flag_zero


def test_add_with_zero(vm):
    vm.registers[7] = -4
    vm.registers[3] = 4
    vm.exec_one(Op('ADD', ['R5', 'R7', 'R3']))
    assert vm.registers[5] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_add_with_overflow(vm):
    vm.registers[9] = 32767
    vm.registers[2] = 1
    vm.exec_one(Op('ADD', ['R7', 'R9', 'R2']))
    assert vm.registers[7] == -32768
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_big_overflow(vm):
    vm.registers[9] = 32767
    vm.registers[2] = 32767
    vm.exec_one(Op('ADD', ['R7', 'R9', 'R2']))
    assert vm.registers[7] == -2
    assert vm.pc == 1
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_negative_overflow(vm):
    vm.registers[9] = -32768
    vm.registers[2] = -32768
    vm.exec_one(Op('ADD', ['R7', 'R9', 'R2']))
    assert vm.registers[7] == 0
    assert vm.pc == 1
    assert not vm.flag_sign
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


def test_sub_small_numbers(vm):
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 42


def test_sub_sets_flags(vm):
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry


def test_sub_increments_pc(vm):
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.pc == 1


def test_sub_with_negative(vm):
    vm.registers[2] = -64
    vm.registers[3] = 22
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == -86
    assert vm.flag_sign
    assert not vm.flag_zero


def test_sub_with_zero(vm):
    vm.registers[2] = -37
    vm.registers[3] = -37
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


@pytest.mark.skip('')
def test_sub_with_negative_overflow(vm):
    vm.registers[1] = -32000
    vm.registers[2] = 32000
    vm.exec_one(Op('SUB', ['R3', 'R1', 'R2']))
    assert vm.registers[3] == 1535
    assert not vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow
