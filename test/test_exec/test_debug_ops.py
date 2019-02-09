import pytest
from .utils import helper

from hera.data import Settings
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine(Settings(color=False))


def test_exec_print_reg(vm, capsys):
    vm.registers[1] = 70

    helper(vm, "print_reg(R1)")

    assert capsys.readouterr().out == "R1 = 0x0046 = 70 = 'F'\n"


def test_print_reg_increments_pc(vm):
    helper(vm, "print_reg(R1)")

    assert vm.pc == 1


def test_exec_print(vm, capsys):
    helper(vm, 'print("Hello, world!")')

    assert capsys.readouterr().out == "Hello, world!"


def test_print_increments_pc(vm):
    helper(vm, 'print("Hello, world!")')

    assert vm.pc == 1


def test_exec_println(vm, capsys):
    helper(vm, 'println("Hello, world!")')

    assert capsys.readouterr().out == "Hello, world!\n"


def test_println_increments_pc(vm):
    helper(vm, 'println("Hello, world!")')

    assert vm.pc == 1


def test___eval_increments_pc(vm):
    helper(vm, '__eval("0")')

    assert vm.pc == 1
