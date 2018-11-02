from hera.parser import Op
from hera.vm import VirtualMachine


def test_add():
    vm = VirtualMachine()
    vm.registers[2] = 20
    vm.registers[3] = 22
    vm.exec_one(Op('ADD', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 42
    assert vm.pc == 1
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_negative():
    vm = VirtualMachine()
    vm.registers[2] = -14
    vm.registers[3] = 8
    vm.exec_one(Op('ADD', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == -6
    assert vm.pc == 1
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_zero():
    vm = VirtualMachine()
    vm.registers[7] = -4
    vm.registers[3] = 4
    vm.exec_one(Op('ADD', ['R5', 'R7', 'R3']))
    assert vm.registers[5] == 0
    assert vm.pc == 1
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_overflow():
    vm = VirtualMachine()
    vm.registers[9] = 32767
    vm.registers[2] = 1
    vm.exec_one(Op('ADD', ['R7', 'R9', 'R2']))
    assert vm.registers[7] == -32768
    assert vm.pc == 1
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_big_overflow():
    vm = VirtualMachine()
    vm.registers[9] = 32767
    vm.registers[2] = 32767
    vm.exec_one(Op('ADD', ['R7', 'R9', 'R2']))
    assert vm.registers[7] == -2
    assert vm.pc == 1
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry


def test_add_with_negative_overflow():
    vm = VirtualMachine()
    vm.registers[9] = -32768
    vm.registers[2] = -32768
    vm.exec_one(Op('ADD', ['R7', 'R9', 'R2']))
    assert vm.registers[7] == 0
    assert vm.pc == 1
    assert not vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry


def test_sub():
    vm = VirtualMachine()
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 42
    assert vm.pc == 1
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow


def test_sub_with_negative():
    vm = VirtualMachine()
    vm.registers[2] = -64
    vm.registers[3] = 22
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == -86
    assert vm.pc == 1
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow


def test_sub_with_zero():
    vm = VirtualMachine()
    vm.registers[2] = -37
    vm.registers[3] = -37
    vm.exec_one(Op('SUB', ['R1', 'R2', 'R3']))
    assert vm.registers[1] == 0
    assert vm.pc == 1
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
