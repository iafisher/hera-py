import pytest
from .utils import helper

from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_SETLO_with_positive(vm):
    helper(vm, "SETLO(R5, 23)")

    assert vm.registers[5] == 23


def test_SETLO_with_negative(vm):
    helper(vm, "SETLO(R9, -12)")

    assert vm.registers[9] == to_u16(-12)


def test_SETLO_with_max_positive(vm):
    helper(vm, "SETLO(R2, 127)")

    assert vm.registers[2] == 127


def test_SETLO_with_255(vm):
    helper(vm, "SETLO(R2, 255)")

    assert vm.registers[2] == to_u16(-1)


def test_SETLO_with_max_negative(vm):
    helper(vm, "SETLO(R2, -128)")

    assert vm.registers[2] == to_u16(-128)


def test_SETLO_clears_high_bits(vm):
    vm.registers[6] = 4765

    helper(vm, "SETLO(R6, 68)")

    assert vm.registers[6] == 68


def test_SETLO_increments_pc(vm):
    helper(vm, "SETLO(R9, -12)")

    assert vm.pc == 1


def test_SETLO_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False

    helper(vm, "SETLO(R7, 0)")

    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_SETLO_does_not_set_zero_flag(vm):
    helper(vm, "SETLO(R7, 0)")

    assert not vm.flag_zero


def test_SETLO_does_not_set_sign_flag(vm):
    helper(vm, "SETLO(R7, -1)")

    assert not vm.flag_sign


def test_SETLO_does_not_change_R0(vm):
    helper(vm, "SETLO(R0, 20)")

    assert vm.registers[0] == 0


def test_SETHI_with_positive(vm):
    helper(vm, "SETHI(R5, 23)")

    assert vm.registers[5] == 5888


def test_SETHI_with_max_positive(vm):
    helper(vm, "SETHI(R2, 255)")

    assert vm.registers[2] == 65280


def test_SETHI_does_not_clear_low_bits(vm):
    vm.registers[6] = 4765

    helper(vm, "SETHI(R6, 68)")

    assert vm.registers[6] == 17565


def test_SETHI_increments_pc(vm):
    helper(vm, "SETHI(R9, 12)")

    assert vm.pc == 1


def test_SETHI_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False

    helper(vm, "SETHI(R7, 0)")

    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_SETHI_does_not_set_zero_flag(vm):
    helper(vm, "SETHI(R7, 0)")

    assert not vm.flag_zero


def test_SETHI_does_not_set_sign_flag(vm):
    helper(vm, "SETHI(R7, -1)")

    assert not vm.flag_sign


def test_SETHI_does_not_change_R0(vm):
    helper(vm, "SETHI(R0, 20)")

    assert vm.registers[0] == 0


def test_INC_with_small_positive(vm):
    helper(vm, "INC(R8, 6)")

    assert vm.registers[8] == 6


def test_INC_with_max(vm):
    helper(vm, "INC(R2, 32)")

    assert vm.registers[2] == 32


def test_INC_with_previous_value(vm):
    vm.registers[5] = 4000

    helper(vm, "INC(R5, 2)")

    assert vm.registers[5] == 4002


def test_INC_with_previous_negative_value(vm):
    vm.registers[9] = to_u16(-12)

    helper(vm, "INC(R9, 10)")

    assert vm.registers[9] == to_u16(-2)


def test_INC_increments_pc(vm):
    helper(vm, "INC(R1, 1)")

    assert vm.pc == 1


def test_INC_sets_zero_flag(vm):
    vm.registers[7] = to_u16(-1)

    helper(vm, "INC(R7, 1)")

    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_INC_sets_sign_flag(vm):
    vm.registers[1] = 32765

    helper(vm, "INC(R1, 5)")

    assert vm.registers[1] == to_u16(-32766)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_INC_sets_carry_flag(vm):
    vm.registers[8] = to_u16(-1)

    helper(vm, "INC(R8, 1)")

    assert vm.flag_carry
    assert not vm.flag_overflow


def test_INC_sets_overflow_flag(vm):
    vm.registers[8] = 32765

    helper(vm, "INC(R8, 5)")

    assert not vm.flag_carry
    assert vm.flag_overflow


def test_INC_ignores_incoming_carry(vm):
    vm.flag_carry = True

    helper(vm, "INC(R8, 5)")

    assert vm.registers[8] == 5
    assert not vm.flag_carry


def test_INC_does_not_affect_R0(vm):
    helper(vm, "INC(R0, 1)")

    assert vm.registers[0] == 0


def test_DEC_with_small_positive(vm):
    helper(vm, "DEC(R8, 6)")

    assert vm.registers[8] == to_u16(-6)


def test_DEC_with_max(vm):
    helper(vm, "DEC(R2, 32)")

    assert vm.registers[2] == to_u16(-32)


def test_DEC_with_previous_value(vm):
    vm.registers[5] = 4000

    helper(vm, "DEC(R5, 2)")

    assert vm.registers[5] == 3998


def test_DEC_with_previous_negative_value(vm):
    vm.registers[9] = to_u16(-12)

    helper(vm, "DEC(R9, 10)")

    assert vm.registers[9] == to_u16(-22)


def test_DEC_increments_pc(vm):
    helper(vm, "DEC(R1, 1)")

    assert vm.pc == 1


def test_DEC_sets_zero_flag(vm):
    vm.registers[7] = 1

    helper(vm, "DEC(R7, 1)")

    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_DEC_sets_sign_flag(vm):
    vm.registers[1] = 1

    helper(vm, "DEC(R1, 5)")

    assert vm.registers[1] == to_u16(-4)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_DEC_sets_carry_flag(vm):
    helper(vm, "DEC(R8, 1)")

    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_DEC_sets_overflow_flag(vm):
    vm.registers[8] = to_u16(-32768)

    helper(vm, "DEC(R8, 5)")

    assert vm.registers[8] == 32763
    assert vm.flag_carry
    assert vm.flag_overflow


def test_DEC_ignores_incoming_carry(vm):
    vm.flag_carry = True

    helper(vm, "DEC(R8, 5)")

    assert vm.registers[8] == to_u16(-5)
    assert not vm.flag_carry


def test_DEC_does_not_affect_R0(vm):
    helper(vm, "DEC(R0, 1)")

    assert vm.registers[0] == 0
