import pytest

from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_print_reg_increments_pc(vm):
    vm.exec_print_reg("R1")
    assert vm.pc == 1


def test_print_increments_pc(vm):
    vm.exec_print("Hello, world!")
    assert vm.pc == 1


def test_println_increments_pc(vm):
    vm.exec_println("Hello, world!")
    assert vm.pc == 1
