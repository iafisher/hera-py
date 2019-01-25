import pytest

from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_print_reg(vm, capsys):
    vm.registers[1] = 70

    vm.exec_print_reg("R1")

    assert capsys.readouterr().out == "R1 = 0x0046 = 70 = 'F'\n"


def test_print_reg_increments_pc(vm):
    vm.exec_print_reg("R1")
    assert vm.pc == 1


def test_exec_print(vm, capsys):
    vm.exec_print("Hello, world!")
    assert capsys.readouterr().out == "Hello, world!"


def test_print_increments_pc(vm):
    vm.exec_print("Hello, world!")
    assert vm.pc == 1


def test_exec_println(vm, capsys):
    vm.exec_println("Hello, world!")
    assert capsys.readouterr().out == "Hello, world!\n"


def test_println_increments_pc(vm):
    vm.exec_println("Hello, world!")
    assert vm.pc == 1


def test___eval(vm):
    vm.exec___eval("vm.registers[7] = 10")
    assert vm.registers[7] == 10


def test___eval_cannot_import_anything(vm, capsys):
    vm.exec___eval("import sys; sys.stdout.write('hi')")
    assert capsys.readouterr().out == ""


def test___eval_increments_pc(vm):
    vm.exec___eval("")
    assert vm.pc == 1
