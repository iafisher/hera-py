import pytest
from .utils import helper

from hera.data import DEFAULT_DATA_START
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_INTEGER_fills_in_memory(vm):
    helper(vm, "INTEGER(42)")

    assert vm.memory[DEFAULT_DATA_START] == 42


def test_INTEGER_increments_data_counter(vm):
    helper(vm, "INTEGER(42)")

    assert vm.dc == DEFAULT_DATA_START + 1


def test_INTEGER_increments_pc(vm):
    helper(vm, "INTEGER(42)")

    assert vm.pc == 1


def test_DSKIP_increments_data_counter(vm):
    helper(vm, "DSKIP(10)")

    assert vm.dc == DEFAULT_DATA_START + 10


def test_DSKIP_increments_pc(vm):
    helper(vm, "DSKIP(10)")

    assert vm.pc == 1


def test_LP_STRING_fills_in_memory(vm):
    helper(vm, 'LP_STRING("hello")')

    assert vm.memory[DEFAULT_DATA_START] == 5
    assert vm.memory[DEFAULT_DATA_START + 1] == ord("h")
    assert vm.memory[DEFAULT_DATA_START + 2] == ord("e")
    assert vm.memory[DEFAULT_DATA_START + 3] == ord("l")
    assert vm.memory[DEFAULT_DATA_START + 4] == ord("l")
    assert vm.memory[DEFAULT_DATA_START + 5] == ord("o")


def test_LP_STRING_increments_data_counter(vm):
    helper(vm, 'LP_STRING("hello")')

    assert vm.dc == DEFAULT_DATA_START + 6


def test_LP_STRING_increments_pc(vm):
    helper(vm, 'LP_STRING("hello")')

    assert vm.pc == 1
