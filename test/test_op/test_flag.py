import pytest
from unittest.mock import patch
from .utils import helper

from hera.data import Op
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_SAVEF_with_sign(vm):
    vm.flag_sign = True

    helper(vm, "SAVEF(R5)")

    assert vm.registers[5] == 1
    assert vm.flag_sign


def test_SAVEF_with_zero(vm):
    vm.flag_zero = True

    helper(vm, "SAVEF(R5)")

    assert vm.registers[5] == 0b10
    assert vm.flag_zero


def test_SAVEF_with_overflow(vm):
    vm.flag_overflow = True

    helper(vm, "SAVEF(R5)")

    assert vm.registers[5] == 0b100
    assert vm.flag_overflow


def test_SAVEF_with_carry(vm):
    vm.flag_carry = True

    helper(vm, "SAVEF(R5)")

    assert vm.registers[5] == 0b1000
    assert vm.flag_carry


def test_SAVEF_with_carry_block(vm):
    vm.flag_carry_block = True

    helper(vm, "SAVEF(R5)")

    assert vm.registers[5] == 0b10000


def test_SAVEF_with_several_flags(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True

    helper(vm, "SAVEF(R5)")

    assert vm.registers[5] == 0b1101
    assert vm.flag_sign
    assert vm.flag_overflow
    assert vm.flag_carry


def test_SAVEF_with_all_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True

    helper(vm, "SAVEF(R5)")

    assert vm.registers[5] == 0b11111
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_SAVEF_with_no_flags(vm):
    helper(vm, "SAVEF(R5)")

    assert vm.registers[5] == 0


def test_SAVEF_overwrites_high_bits(vm):
    vm.registers[5] = 17500

    helper(vm, "SAVEF(R5)")

    assert vm.registers[5] == 0


def test_SAVEF_increments_pc(vm):
    helper(vm, "SAVEF(R5)")

    assert vm.pc == 1


def test_SAVEF_does_not_affect_R0(vm):
    vm.flag_carry = True

    helper(vm, "SAVEF(R0)")

    assert vm.registers[0] == 0


def test_RSTRF_with_sign(vm):
    vm.registers[5] = 1

    helper(vm, "RSTRF(R5)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_RSTRF_with_zero(vm):
    vm.registers[5] = 0b10

    helper(vm, "RSTRF(R5)")

    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_RSTRF_with_overflow(vm):
    vm.registers[5] = 0b100

    helper(vm, "RSTRF(R5)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_RSTRF_with_carry(vm):
    vm.registers[5] = 0b1000

    helper(vm, "RSTRF(R5)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_RSTRF_with_carry_block(vm):
    vm.registers[5] = 0b10000

    helper(vm, "RSTRF(R5)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_RSTRF_with_several_flags(vm):
    vm.registers[5] = 0b1101

    helper(vm, "RSTRF(R5)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_RSTRF_with_all_flags(vm):
    vm.registers[5] = 0b11111

    helper(vm, "RSTRF(R5)")

    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_RSTRF_with_no_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True

    helper(vm, "RSTRF(R5)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_RSTRF_increments_pc(vm):
    helper(vm, "RSTRF(R5)")

    assert vm.pc == 1


def test_FON_with_sign(vm):
    helper(vm, "FON(1)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FON_with_zero(vm):
    helper(vm, "FON(0b10)")

    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FON_with_overflow(vm):
    helper(vm, "FON(0b100)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FON_with_carry(vm):
    helper(vm, "FON(0b1000)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_FON_with_carry_block(vm):
    helper(vm, "FON(0b10000)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_FON_with_multiple_flags(vm):
    helper(vm, "FON(0b10101)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_FON_with_no_flags(vm):
    helper(vm, "FON(0)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FON_does_not_overwrite_flags(vm):
    vm.flag_carry_block = True

    helper(vm, "FON(1)")

    assert vm.flag_sign
    assert vm.flag_carry_block


def test_FON_increments_pc(vm):
    helper(vm, "FON(0)")

    assert vm.pc == 1


def test_FOFF_with_sign(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True

    helper(vm, "FOFF(1)")

    assert not vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_FOFF_with_zero(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True

    helper(vm, "FOFF(0b10)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_FOFF_with_overflow(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True

    helper(vm, "FOFF(0b100)")

    assert vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_FOFF_with_carry(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True

    helper(vm, "FOFF(0b1000)")

    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_FOFF_with_carry_block(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True

    helper(vm, "FOFF(0b10000)")

    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_FOFF_with_multiple_flags(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True

    helper(vm, "FOFF(0b10101)")

    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_FOFF_with_no_flags(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True

    helper(vm, "FOFF(0)")

    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_FOFF_increments_pc(vm):
    helper(vm, "FOFF(0)")

    assert vm.pc == 1


def test_FSET5_with_sign(vm):
    helper(vm, "FSET5(1)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET5_with_zero(vm):
    helper(vm, "FSET5(0b10)")

    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET5_with_overflow(vm):
    helper(vm, "FSET5(0b100)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET5_with_carry(vm):
    helper(vm, "FSET5(0b1000)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET5_with_carry_block(vm):
    helper(vm, "FSET5(0b10000)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_FSET5_with_multiple_flags(vm):
    helper(vm, "FSET5(0b10101)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_FSET5_with_no_flags(vm):
    helper(vm, "FSET5(0)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET5_does_overwrite_flags(vm):
    vm.flag_zero = True
    vm.flag_carry_block = True

    helper(vm, "FSET5(1)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_carry_block


def test_FSET5_increments_pc(vm):
    helper(vm, "FSET5(0)")

    assert vm.pc == 1


def test_FSET4_with_sign(vm):
    helper(vm, "FSET4(1)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET4_with_zero(vm):
    helper(vm, "FSET4(0b10)")

    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET4_with_overflow(vm):
    helper(vm, "FSET4(0b100)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET4_with_carry(vm):
    helper(vm, "FSET4(0b1000)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET4_with_multiple_flags(vm):
    helper(vm, "FSET4(0b0101)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET4_with_no_flags(vm):
    helper(vm, "FSET4(0)")

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_FSET4_does_overwrite_flags(vm):
    vm.flag_zero = True
    vm.flag_overflow = True

    helper(vm, "FSET4(1)")

    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow


def test_FSET4_increments_pc(vm):
    helper(vm, "FSET4(0)")

    assert vm.pc == 1
