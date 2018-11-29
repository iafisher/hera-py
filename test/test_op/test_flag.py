import pytest
from unittest.mock import patch

from hera.parser import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_savef(vm):
    with patch("hera.vm.VirtualMachine.exec_savef") as mock_exec_savef:
        vm.exec_one(Op("SAVEF", ["R1"]))
        assert mock_exec_savef.call_count == 1
        assert mock_exec_savef.call_args == (("R1",), {})


def test_savef_with_sign(vm):
    vm.flag_sign = True
    vm.exec_savef("R5")
    assert vm.registers[5] == 1
    assert vm.flag_sign


def test_savef_with_zero(vm):
    vm.flag_zero = True
    vm.exec_savef("R5")
    assert vm.registers[5] == 0b10
    assert vm.flag_zero


def test_savef_with_overflow(vm):
    vm.flag_overflow = True
    vm.exec_savef("R5")
    assert vm.registers[5] == 0b100
    assert vm.flag_overflow


def test_savef_with_carry(vm):
    vm.flag_carry = True
    vm.exec_savef("R5")
    assert vm.registers[5] == 0b1000
    assert vm.flag_carry


def test_savef_with_carry_block(vm):
    vm.flag_carry_block = True
    vm.exec_savef("R5")
    assert vm.registers[5] == 0b10000


def test_savef_with_several_flags(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.exec_savef("R5")
    assert vm.registers[5] == 0b1101
    assert vm.flag_sign
    assert vm.flag_overflow
    assert vm.flag_carry


def test_savef_with_all_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_savef("R5")
    assert vm.registers[5] == 0b11111
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_savef_with_no_flags(vm):
    vm.exec_savef("R5")
    assert vm.registers[5] == 0


def test_savef_overwrites_high_bits(vm):
    vm.registers[5] = 17500
    vm.exec_savef("R5")
    assert vm.registers[5] == 0


def test_savef_increments_pc(vm):
    vm.exec_savef("R5")
    assert vm.pc == 1


def test_savef_does_not_affect_R0(vm):
    vm.flag_carry = True
    vm.exec_savef("R0")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_rstrf(vm):
    with patch("hera.vm.VirtualMachine.exec_rstrf") as mock_exec_rstrf:
        vm.exec_one(Op("RSTRF", ["R1"]))
        assert mock_exec_rstrf.call_count == 1
        assert mock_exec_rstrf.call_args == (("R1",), {})


def test_rstrf_with_sign(vm):
    vm.registers[5] = 1
    vm.exec_rstrf("R5")
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_zero(vm):
    vm.registers[5] = 0b10
    vm.exec_rstrf("R5")
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_overflow(vm):
    vm.registers[5] = 0b100
    vm.exec_rstrf("R5")
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_carry(vm):
    vm.registers[5] = 0b1000
    vm.exec_rstrf("R5")
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_carry_block(vm):
    vm.registers[5] = 0b10000
    vm.exec_rstrf("R5")
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_rstrf_with_several_flags(vm):
    vm.registers[5] = 0b1101
    vm.exec_rstrf("R5")
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_with_all_flags(vm):
    vm.registers[5] = 0b11111
    vm.exec_rstrf("R5")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_rstrf_with_no_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_rstrf("R5")
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_rstrf_increments_pc(vm):
    vm.exec_rstrf("R5")
    assert vm.pc == 1


def test_exec_one_delegates_to_fon(vm):
    with patch("hera.vm.VirtualMachine.exec_fon") as mock_exec_fon:
        vm.exec_one(Op("FON", [5]))
        assert mock_exec_fon.call_count == 1
        assert mock_exec_fon.call_args == ((5,), {})


def test_fon_with_sign(vm):
    vm.exec_fon(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_with_zero(vm):
    vm.exec_fon(0b10)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_with_overflow(vm):
    vm.exec_fon(0b100)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_with_carry(vm):
    vm.exec_fon(0b1000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_with_carry_block(vm):
    vm.exec_fon(0b10000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_fon_with_multiple_flags(vm):
    vm.exec_fon(0b10101)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_fon_with_no_flags(vm):
    vm.exec_fon(0)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fon_does_not_overwrite_flags(vm):
    vm.flag_carry_block = True
    vm.exec_fon(1)
    assert vm.flag_sign
    assert vm.flag_carry_block


def test_fon_increments_pc(vm):
    vm.exec_fon(0)
    assert vm.pc == 1


def test_exec_one_delegates_to_foff(vm):
    with patch("hera.vm.VirtualMachine.exec_foff") as mock_exec_foff:
        vm.exec_one(Op("FOFF", [5]))
        assert mock_exec_foff.call_count == 1
        assert mock_exec_foff.call_args == ((5,), {})


def test_foff_with_sign(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(1)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_foff_with_zero(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b10)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_foff_with_overflow(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b100)
    assert vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_foff_with_carry(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b1000)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_foff_with_carry_block(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b10000)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_foff_with_multiple_flags(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0b10101)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_foff_with_no_flags(vm):
    vm.flag_zero = True
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_foff(0)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_foff_increments_pc(vm):
    vm.exec_foff(0)
    assert vm.pc == 1


def test_exec_one_delegates_to_fset5(vm):
    with patch("hera.vm.VirtualMachine.exec_fset5") as mock_exec_fset5:
        vm.exec_one(Op("FSET5", [5]))
        assert mock_exec_fset5.call_count == 1
        assert mock_exec_fset5.call_args == ((5,), {})


def test_fset5_with_sign(vm):
    vm.exec_fset5(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_with_zero(vm):
    vm.exec_fset5(0b10)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_with_overflow(vm):
    vm.exec_fset5(0b100)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_with_carry(vm):
    vm.exec_fset5(0b1000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_with_carry_block(vm):
    vm.exec_fset5(0b10000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_fset5_with_multiple_flags(vm):
    vm.exec_fset5(0b10101)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_fset5_with_no_flags(vm):
    vm.exec_fset5(0)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset5_does_overwrite_flags(vm):
    vm.flag_zero = True
    vm.flag_carry_block = True
    vm.exec_fset5(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_carry_block


def test_fset5_increments_pc(vm):
    vm.exec_fset5(0)
    assert vm.pc == 1


def test_exec_one_delegates_to_fset4(vm):
    with patch("hera.vm.VirtualMachine.exec_fset4") as mock_exec_fset4:
        vm.exec_one(Op("FSET4", [5]))
        assert mock_exec_fset4.call_count == 1
        assert mock_exec_fset4.call_args == ((5,), {})


def test_fset4_with_sign(vm):
    vm.exec_fset4(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_zero(vm):
    vm.exec_fset4(0b10)
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_overflow(vm):
    vm.exec_fset4(0b100)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_carry(vm):
    vm.exec_fset4(0b1000)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_multiple_flags(vm):
    vm.exec_fset4(0b101)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_with_no_flags(vm):
    vm.exec_fset4(0)
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_fset4_does_overwrite_flags(vm):
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.exec_fset4(1)
    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow


def test_fset4_increments_pc(vm):
    vm.exec_fset4(0)
    assert vm.pc == 1
