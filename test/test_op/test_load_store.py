import pytest
from unittest.mock import patch

from hera.data import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_LOAD(vm):
    with patch("hera.vm.VirtualMachine.exec_LOAD") as mock_exec_LOAD:
        vm.exec_one(Op("LOAD", ["R1", 0, "R2"]))
        assert mock_exec_LOAD.call_count == 1
        assert mock_exec_LOAD.call_args == (("R1", 0, "R2"), {})


def test_LOAD_from_small_address(vm):
    vm.memory[3] = 42
    vm.registers[2] = 3
    vm.exec_LOAD("R1", 0, "R2")
    assert vm.registers[1] == 42


def test_LOAD_from_uninitialized_address(vm):
    vm.registers[2] = 5
    vm.exec_LOAD("R1", 0, "R2")
    assert vm.registers[1] == 0


def test_LOAD_from_large_uninitialized_address(vm):
    vm.registers[2] = 14000
    vm.exec_LOAD("R1", 0, "R2")
    assert vm.registers[1] == 0


def test_LOAD_from_address_zero(vm):
    vm.memory[0] = 42
    vm.exec_LOAD("R1", 0, "R0")
    assert vm.registers[1] == 42


def test_LOAD_with_offset(vm):
    vm.memory[7] = 42
    vm.registers[2] = 4
    vm.exec_LOAD("R1", 3, "R2")
    assert vm.registers[1] == 42


def test_LOAD_sets_zero_flag(vm):
    vm.exec_LOAD("R1", 0, "R0")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_LOAD_sets_sign_flag(vm):
    vm.memory[4] = to_u16(-2)
    vm.registers[2] = 4
    vm.exec_LOAD("R1", 0, "R2")
    assert vm.registers[1] == to_u16(-2)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_LOAD_ignores_other_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_carry_block = True
    vm.exec_LOAD("R1", 0, "R0")
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_carry_block


def test_LOAD_does_not_affect_R0(vm):
    vm.memory[2] = 5
    vm.registers[2] = 2
    vm.exec_LOAD("R0", 0, "R2")
    assert vm.registers[0] == 0


def test_LOAD_increments_pc(vm):
    vm.exec_LOAD("R1", 0, "R2")
    assert vm.pc == 1


def test_exec_one_delegates_to_STORE(vm):
    with patch("hera.vm.VirtualMachine.exec_STORE") as mock_exec_STORE:
        vm.exec_one(Op("STORE", ["R1", 0, "R2"]))
        assert mock_exec_STORE.call_count == 1
        assert mock_exec_STORE.call_args == (("R1", 0, "R2"), {})


def test_STORE_to_small_address(vm):
    vm.registers[1] = 42
    vm.registers[2] = 3
    vm.exec_STORE("R1", 0, "R2")
    assert vm.memory[3] == 42


def test_STORE_to_large_address(vm):
    vm.registers[1] = 42
    vm.registers[2] = 5000
    vm.exec_STORE("R1", 0, "R2")
    assert vm.memory[5000] == 42


def test_STORE_to_max_address(vm):
    vm.registers[1] = 42
    vm.registers[2] = (2 ** 16) - 1
    vm.exec_STORE("R1", 0, "R2")
    assert vm.memory[(2 ** 16) - 1] == 42


def test_STORE_to_address_zero(vm):
    vm.registers[1] = 42
    vm.exec_STORE("R1", 0, "R0")
    assert vm.memory[0] == 42


def test_STORE_with_offset(vm):
    vm.registers[1] = 42
    vm.registers[2] = 4
    vm.exec_STORE("R1", 3, "R2")
    assert vm.memory[7] == 42


def test_STORE_ignores_all_flags(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_carry_block = True
    vm.registers[1] = 42
    vm.exec_STORE("R1", 0, "R0")
    assert vm.flag_zero
    assert vm.flag_sign
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_carry_block


def test_STORE_increments_pc(vm):
    vm.exec_STORE("R1", 0, "R2")
    assert vm.pc == 1
