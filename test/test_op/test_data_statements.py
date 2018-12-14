import pytest

from hera.parser import Op
from hera.symtab import HERA_DATA_START
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_integer_fills_in_memory(vm):
    vm.exec_integer(42)
    assert vm.memory[HERA_DATA_START] == 42


def test_integer_increments_data_counter(vm):
    vm.exec_integer(42)
    assert vm.dc == HERA_DATA_START + 1


def test_integer_increments_pc(vm):
    vm.exec_integer(42)
    assert vm.pc == 1


def test_dskip_increments_data_counter(vm):
    vm.exec_dskip(10)
    assert vm.dc == HERA_DATA_START + 10


def test_dskip_increments_pc(vm):
    vm.exec_dskip(10)
    assert vm.pc == 1


def test_lp_string_fills_in_memory(vm):
    vm.exec_lp_string("hello")
    assert vm.memory[HERA_DATA_START] == 5
    assert vm.memory[HERA_DATA_START + 1] == ord("h")
    assert vm.memory[HERA_DATA_START + 2] == ord("e")
    assert vm.memory[HERA_DATA_START + 3] == ord("l")
    assert vm.memory[HERA_DATA_START + 4] == ord("l")
    assert vm.memory[HERA_DATA_START + 5] == ord("o")


def test_lp_string_increments_data_counter(vm):
    vm.exec_lp_string("hello")
    assert vm.dc == HERA_DATA_START + 6


def test_lp_string_increments_pc(vm):
    vm.exec_lp_string("hello")
    assert vm.pc == 1
