import pytest
from unittest.mock import patch

from hera.parser import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_load(vm):
    with patch("hera.vm.VirtualMachine.exec_load") as mock_exec_load:
        vm.exec_one(Op("LOAD", ["R1", 0, "R2"]))
        assert mock_exec_load.call_count == 1
        assert mock_exec_load.call_args == (("R1", 0, "R2"), {})


def test_load_from_small_address(vm):
    vm.memory[3] = 42
    vm.registers[2] = 3
    vm.exec_load("R1", 0, "R2")
    assert vm.registers[1] == 42


def test_load_from_uninitialized_address(vm):
    vm.registers[2] = 5
    vm.exec_load("R1", 0, "R2")
    assert vm.registers[1] == 0


def test_load_from_large_uninitialized_address(vm):
    vm.registers[2] = 14000
    vm.exec_load("R1", 0, "R2")
    assert vm.registers[1] == 0


def test_load_from_address_zero(vm):
    vm.memory[0] = 42
    vm.exec_load("R1", 0, "R0")
    assert vm.registers[1] == 42


def test_load_with_offset(vm):
    vm.memory[7] = 42
    vm.registers[2] = 4
    vm.exec_load("R1", 3, "R2")
    assert vm.registers[1] == 42


def test_load_sets_zero_flag(vm):
    vm.exec_load("R1", 0, "R0")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_load_sets_sign_flag(vm):
    vm.memory[4] = to_u16(-2)
    vm.registers[2] = 4
    vm.exec_load("R1", 0, "R2")
    assert vm.registers[1] == to_u16(-2)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_load_ignores_other_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_carry_block = True
    vm.exec_load("R1", 0, "R0")
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_carry_block


def test_load_does_not_affect_R0(vm):
    vm.memory[2] = 5
    vm.registers[2] = 2
    vm.exec_load("R0", 0, "R2")
    assert vm.registers[0] == 0


def test_load_increments_pc(vm):
    vm.exec_load("R1", 0, "R2")
    assert vm.pc == 1


def test_exec_one_delegates_to_store(vm):
    with patch("hera.vm.VirtualMachine.exec_store") as mock_exec_store:
        vm.exec_one(Op("STORE", ["R1", 0, "R2"]))
        assert mock_exec_store.call_count == 1
        assert mock_exec_store.call_args == (("R1", 0, "R2"), {})


def test_store_to_small_address(vm):
    vm.registers[1] = 42
    vm.registers[2] = 3
    vm.exec_store("R1", 0, "R2")
    assert vm.memory[3] == 42


def test_store_to_large_address(vm):
    vm.registers[1] = 42
    vm.registers[2] = 5000
    vm.exec_store("R1", 0, "R2")
    assert vm.memory[5000] == 42


def test_store_to_max_address(vm):
    vm.registers[1] = 42
    vm.registers[2] = (2 ** 16) - 1
    vm.exec_store("R1", 0, "R2")
    assert vm.memory[(2 ** 16) - 1] == 42


def test_store_to_address_zero(vm):
    vm.registers[1] = 42
    vm.exec_store("R1", 0, "R0")
    assert vm.memory[0] == 42


def test_store_with_offset(vm):
    vm.registers[1] = 42
    vm.registers[2] = 4
    vm.exec_store("R1", 3, "R2")
    assert vm.memory[7] == 42


def test_store_ignores_all_flags(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_carry_block = True
    vm.registers[1] = 42
    vm.exec_store("R1", 0, "R0")
    assert vm.flag_zero
    assert vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_carry_block


def test_store_increments_pc(vm):
    vm.exec_store("R1", 0, "R2")
    assert vm.pc == 1
