from hera.parser import Op
from hera.vm import VirtualMachine


def test_add():
    vm = VirtualMachine()
    vm.registers[2] = 20
    vm.registers[3] = 22
    vm.exec_one(Op('ADD', [1, 2, 3]))
    assert vm.registers[1] == 42
    assert vm.pc == 1


def test_sub():
    vm = VirtualMachine()
    vm.registers[2] = 64
    vm.registers[3] = 22
    vm.exec_one(Op('SUB', [1, 2, 3]))
    assert vm.registers[1] == 42
    assert vm.pc == 1
