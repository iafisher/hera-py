import pytest
from .utils import helper

from hera.data import Token
from hera.op import name_to_class
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def branch_helper(vm, branchname):
    op = name_to_class[branchname](Token.Sym("l"))
    return op.should(vm)


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
    assert branch_helper(vm, "BL")


def test_should_BL_on_overflow(vm):
    vm.flag_overflow = True
    assert branch_helper(vm, "BL")


def test_should_not_BL_on_sign_and_overflow(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    assert not branch_helper(vm, "BL")


def test_should_not_BL_on_neither_sign_nor_overflow(vm):
    vm.flag_sign = False
    vm.flag_overflow = False
    assert not branch_helper(vm, "BL")


def test_should_BGE_on_no_flags(vm):
    assert branch_helper(vm, "BGE")


def test_should_BGE_on_sign_and_overflow(vm):
    vm.flag_overflow = True
    vm.flag_sign = True
    assert branch_helper(vm, "BGE")


def test_should_not_BGE_on_sign(vm):
    vm.flag_sign = True
    assert not branch_helper(vm, "BGE")


def test_should_not_BGE_on_overflow(vm):
    vm.flag_overflow = True
    assert not branch_helper(vm, "BGE")


def test_should_BGE_on_zero(vm):
    vm.flag_zero = True
    assert branch_helper(vm, "BGE")


def test_should_BLE_on_sign(vm):
    vm.flag_sign = True
    assert branch_helper(vm, "BLE")


def test_should_BLE_on_overflow(vm):
    vm.flag_overflow = True
    assert branch_helper(vm, "BLE")


def test_should_BLE_on_zero(vm):
    vm.flag_zero = True
    assert branch_helper(vm, "BLE")


def test_should_BLE_on_overflow_and_zero(vm):
    vm.flag_overflow = True
    vm.flag_zero = True
    assert branch_helper(vm, "BLE")


def test_should_not_BLE_on_no_flags(vm):
    assert not branch_helper(vm, "BLE")


def test_should_not_BLE_on_sign_and_overflow(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    assert not branch_helper(vm, "BLE")


def test_should_BG_on_no_flags(vm):
    assert branch_helper(vm, "BG")


def test_should_BG_on_sign_and_overflow(vm):
    vm.flag_overflow = True
    vm.flag_sign = True
    assert branch_helper(vm, "BG")


def test_should_not_BG_on_sign(vm):
    vm.flag_sign = True
    assert not branch_helper(vm, "BG")


def test_should_not_BG_on_overflow(vm):
    vm.flag_overflow = True
    assert not branch_helper(vm, "BG")


def test_should_not_BG_on_zero(vm):
    vm.flag_zero = True
    assert not branch_helper(vm, "BG")


def test_should_BULE_on_not_carry(vm):
    vm.flag_carry = False
    assert branch_helper(vm, "BULE")


def test_should_not_BULE_on_overflow(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    assert not branch_helper(vm, "BULE")


def test_should_BULE_on_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = True
    assert branch_helper(vm, "BULE")


def test_should_not_BULE_on_sign_and_carry(vm):
    vm.flag_carry = True
    vm.flag_sign = True
    assert not branch_helper(vm, "BULE")


def test_should_BUG_on_carry_and_not_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = False
    assert branch_helper(vm, "BUG")


def test_should_not_BUG_on_carry_and_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = True
    assert not branch_helper(vm, "BUG")


def test_should_not_BUG_on_not_carry_and_not_zero(vm):
    vm.flag_carry = False
    vm.flag_zero = False
    assert not branch_helper(vm, "BUG")


def test_should_not_BUG_on_sign(vm):
    vm.flag_sign = True
    assert not branch_helper(vm, "BUG")


def test_should_BZ_on_zero(vm):
    vm.flag_zero = True
    assert branch_helper(vm, "BZ")


def test_should_not_BZ_on_not_zero(vm):
    vm.flag_zero = False
    assert not branch_helper(vm, "BZ")


def test_should_BC_on_carry(vm):
    vm.flag_carry = True
    assert branch_helper(vm, "BC")


def test_should_not_BC_on_not_carry(vm):
    vm.flag_carry = False
    assert not branch_helper(vm, "BC")


def test_should_BS_on_sign(vm):
    vm.flag_sign = True
    assert branch_helper(vm, "BS")


def test_should_not_BS_on_not_sign(vm):
    vm.flag_sign = False
    assert not branch_helper(vm, "BS")


def test_should_BV_on_overflow(vm):
    vm.flag_overflow = True
    assert branch_helper(vm, "BV")


def test_should_not_BV_on_not_overflow(vm):
    vm.flag_overflow = False
    assert not branch_helper(vm, "BV")


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
