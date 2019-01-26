import pytest
from unittest.mock import patch
from .utils import helper

from hera.data import Op
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_branch_with_register_branch(vm):
    vm.registers[7] = 42
    vm.flag_zero = True

    helper(vm, "BZ(R7)")

    assert vm.pc == 42
    assert vm.flag_zero


def test_exec_branch_with_relative_branch(vm):
    vm.pc = 20
    vm.flag_carry = False

    helper(vm, "BNCR(22)")

    assert vm.pc == 42
    assert not vm.flag_carry


def test_should_BL_on_sign(vm):
    vm.flag_sign = True
    assert vm.should_BL()


def test_should_BL_on_overflow(vm):
    vm.flag_overflow = True
    assert vm.should_BL()


def test_should_not_BL_on_sign_and_overflow(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    assert not vm.should_BL()


def test_should_not_BL_on_neither_sign_nor_overflow(vm):
    vm.flag_sign = False
    vm.flag_overflow = False
    assert not vm.should_BL()


def test_should_BGE_on_no_flags(vm):
    assert vm.should_BGE()


def test_should_BGE_on_sign_and_overflow(vm):
    vm.flag_overflow = True
    vm.flag_sign = True
    assert vm.should_BGE()


def test_should_not_BGE_on_sign(vm):
    vm.flag_sign = True
    assert not vm.should_BGE()


def test_should_not_BGE_on_overflow(vm):
    vm.flag_overflow = True
    assert not vm.should_BGE()


def test_should_BGE_on_zero(vm):
    vm.flag_zero = True
    assert vm.should_BGE()


def test_should_BLE_on_sign(vm):
    vm.flag_sign = True
    assert vm.should_BLE()


def test_should_BLE_on_overflow(vm):
    vm.flag_overflow = True
    assert vm.should_BLE()


def test_should_BLE_on_zero(vm):
    vm.flag_zero = True
    assert vm.should_BLE()


def test_should_BLE_on_overflow_and_zero(vm):
    vm.flag_overflow = True
    vm.flag_zero = True
    assert vm.should_BLE()


def test_should_not_BLE_on_no_flags(vm):
    assert not vm.should_BLE()


def test_should_not_BLE_on_sign_and_overflow(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    assert not vm.should_BLE()


def test_should_BG_on_no_flags(vm):
    assert vm.should_BG()


def test_should_BG_on_sign_and_overflow(vm):
    vm.flag_overflow = True
    vm.flag_sign = True
    assert vm.should_BG()


def test_should_not_BG_on_sign(vm):
    vm.flag_sign = True
    assert not vm.should_BG()


def test_should_not_BG_on_overflow(vm):
    vm.flag_overflow = True
    assert not vm.should_BG()


def test_should_not_BG_on_zero(vm):
    vm.flag_zero = True
    assert not vm.should_BG()


def test_should_BULE_on_not_carry(vm):
    vm.flag_carry = False
    assert vm.should_BULE()


def test_should_not_BULE_on_overflow(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    assert not vm.should_BULE()


def test_should_BULE_on_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = True
    assert vm.should_BULE()


def test_should_not_BULE_on_sign_and_carry(vm):
    vm.flag_carry = True
    vm.flag_sign = True
    assert not vm.should_BULE()


def test_should_BUG_on_carry_and_not_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = False
    assert vm.should_BUG()


def test_should_not_BUG_on_carry_and_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = True
    assert not vm.should_BUG()


def test_should_not_BUG_on_not_carry_and_not_zero(vm):
    vm.flag_carry = False
    vm.flag_zero = False
    assert not vm.should_BUG()


def test_should_not_BUG_on_sign(vm):
    vm.flag_sign = True
    assert not vm.should_BUG()


def test_should_BZ_on_zero(vm):
    vm.flag_zero = True
    assert vm.should_BZ()


def test_should_not_BZ_on_not_zero(vm):
    vm.flag_zero = False
    assert not vm.should_BZ()


def test_should_BC_on_carry(vm):
    vm.flag_carry = True
    assert vm.should_BC()


def test_should_not_BC_on_not_carry(vm):
    vm.flag_carry = False
    assert not vm.should_BC()


def test_should_BS_on_sign(vm):
    vm.flag_sign = True
    assert vm.should_BS()


def test_should_not_BS_on_not_sign(vm):
    vm.flag_sign = False
    assert not vm.should_BS()


def test_should_BV_on_overflow(vm):
    vm.flag_overflow = True
    assert vm.should_BV()


def test_should_not_BV_on_not_overflow(vm):
    vm.flag_overflow = False
    assert not vm.should_BV()


def test_CALL_changes_pc(vm):
    vm.pc = 100
    vm.registers[13] = 40

    helper(vm, "CALL(R12, R13)")

    assert vm.pc == 40


def test_CALL_updates_second_register(vm):
    vm.pc = 100
    vm.registers[13] = 40

    helper(vm, "CALL(R12, R13)")

    assert vm.registers[13] == 101


def test_CALL_updates_frame_pointer(vm):
    vm.registers[12] = 600
    vm.registers[13] = 40

    helper(vm, "CALL(R12, R13)")

    assert vm.registers[14] == 600


def test_CALL_updates_first_register(vm):
    vm.registers[14] = 550
    vm.registers[12] = 600
    vm.registers[13] = 40

    helper(vm, "CALL(R12, R13)")

    assert vm.registers[12] == 550


def test_exec_one_delegates_to_RETURN(vm):
    with patch("hera.vm.VirtualMachine.exec_RETURN") as mock_exec_RETURN:
        helper(vm, "RETURN(R12, R13)")

        assert mock_exec_RETURN.call_count == 1
        assert mock_exec_RETURN.call_args == (("R12", "R13"), {})


def test_RETURN_changes_pc(vm):
    vm.pc = 100
    vm.registers[13] = 40

    helper(vm, "RETURN(R12, R13)")

    assert vm.pc == 40


def test_RETURN_updates_second_register(vm):
    vm.pc = 100
    vm.registers[13] = 40

    helper(vm, "RETURN(R12, R13)")

    assert vm.registers[13] == 101


def test_RETURN_updates_frame_pointer(vm):
    vm.registers[12] = 600
    vm.registers[13] = 40

    helper(vm, "RETURN(R12, R13)")

    assert vm.registers[14] == 600


def test_RETURN_updates_first_register(vm):
    vm.registers[14] = 550
    vm.registers[12] = 600
    vm.registers[13] = 40

    helper(vm, "RETURN(R12, R13)")

    assert vm.registers[12] == 550
