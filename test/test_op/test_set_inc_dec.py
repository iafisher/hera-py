import pytest
from unittest.mock import patch

from hera.parser import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_setlo(vm):
    with patch("hera.vm.VirtualMachine.exec_setlo") as mock_exec_setlo:
        vm.exec_one(Op("SETLO", ["R1", 47]))
        assert mock_exec_setlo.call_count == 1
        assert mock_exec_setlo.call_args == (("R1", 47), {})


def test_setlo_with_positive(vm):
    vm.exec_setlo("R5", 23)
    assert vm.registers[5] == 23


def test_setlo_with_negative(vm):
    vm.exec_setlo("R9", -12)
    assert vm.registers[9] == to_u16(-12)


def test_setlo_with_max_positive(vm):
    vm.exec_setlo("R2", 127)
    assert vm.registers[2] == 127


def test_setlo_with_255(vm):
    vm.exec_setlo("R2", 255)
    assert vm.registers[2] == to_u16(-1)


def test_setlo_with_max_negative(vm):
    vm.exec_setlo("R2", -128)
    assert vm.registers[2] == to_u16(-128)


def test_setlo_clears_high_bits(vm):
    vm.registers[6] = 4765
    vm.exec_setlo("R6", 68)
    assert vm.registers[6] == 68


def test_setlo_increments_pc(vm):
    vm.exec_setlo("R9", -12)
    assert vm.pc == 1


def test_setlo_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False
    vm.exec_setlo("R7", 0)
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_setlo_does_not_set_zero_flag(vm):
    vm.exec_setlo("R7", 0)
    assert not vm.flag_zero


def test_setlo_does_not_set_sign_flag(vm):
    vm.exec_setlo("R7", -1)
    assert not vm.flag_sign


def test_setlo_does_not_change_R0(vm):
    vm.exec_setlo("R0", 20)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_sethi(vm):
    with patch("hera.vm.VirtualMachine.exec_sethi") as mock_exec_sethi:
        vm.exec_one(Op("SETHI", ["R1", 47]))
        assert mock_exec_sethi.call_count == 1
        assert mock_exec_sethi.call_args == (("R1", 47), {})


def test_sethi_with_positive(vm):
    vm.exec_sethi("R5", 23)
    assert vm.registers[5] == 5888


def test_sethi_with_max_positive(vm):
    vm.exec_sethi("R2", 255)
    assert vm.registers[2] == 65280


def test_sethi_does_not_clear_low_bits(vm):
    vm.registers[6] = 4765
    vm.exec_sethi("R6", 68)
    assert vm.registers[6] == 17565


def test_sethi_increments_pc(vm):
    vm.exec_sethi("R9", 12)
    assert vm.pc == 1


def test_sethi_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False
    vm.exec_sethi("R7", 0)
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_sethi_does_not_set_zero_flag(vm):
    vm.exec_sethi("R7", 0)
    assert not vm.flag_zero


def test_sethi_does_not_set_sign_flag(vm):
    vm.exec_sethi("R7", -1)
    assert not vm.flag_sign


def test_sethi_does_not_change_R0(vm):
    vm.exec_sethi("R0", 20)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_inc(vm):
    with patch("hera.vm.VirtualMachine.exec_inc") as mock_exec_inc:
        vm.exec_one(Op("INC", ["R1", 1]))
        assert mock_exec_inc.call_count == 1
        assert mock_exec_inc.call_args == (("R1", 1), {})


def test_inc_with_small_positive(vm):
    vm.exec_inc("R8", 6)
    assert vm.registers[8] == 6


def test_inc_with_max(vm):
    vm.exec_inc("R2", 32)
    assert vm.registers[2] == 32


def test_inc_with_previous_value(vm):
    vm.registers[5] = 4000
    vm.exec_inc("R5", 2)
    assert vm.registers[5] == 4002


def test_inc_with_previous_negative_value(vm):
    vm.registers[9] = to_u16(-12)
    vm.exec_inc("R9", 10)
    assert vm.registers[9] == to_u16(-2)


def test_inc_increments_pc(vm):
    vm.exec_inc("R1", 1)
    assert vm.pc == 1


def test_inc_sets_zero_flag(vm):
    vm.registers[7] = to_u16(-1)
    vm.exec_inc("R7", 1)
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_inc_sets_sign_flag(vm):
    vm.registers[1] = 32765
    vm.exec_inc("R1", 5)
    assert vm.registers[1] == to_u16(-32766)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_inc_sets_carry_flag(vm):
    vm.registers[8] = to_u16(-1)
    vm.exec_inc("R8", 1)
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_inc_sets_overflow_flag(vm):
    vm.registers[8] = 32765
    vm.exec_inc("R8", 5)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_inc_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.exec_inc("R8", 5)
    assert vm.registers[8] == 5
    assert not vm.flag_carry


def test_inc_does_not_affect_R0(vm):
    vm.exec_inc("R0", 1)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_dec(vm):
    with patch("hera.vm.VirtualMachine.exec_dec") as mock_exec_dec:
        vm.exec_one(Op("DEC", ["R1", 1]))
        assert mock_exec_dec.call_count == 1
        assert mock_exec_dec.call_args == (("R1", 1), {})


def test_dec_with_small_positive(vm):
    vm.exec_dec("R8", 6)
    assert vm.registers[8] == to_u16(-6)


def test_dec_with_max(vm):
    vm.exec_dec("R2", 32)
    assert vm.registers[2] == to_u16(-32)


def test_dec_with_previous_value(vm):
    vm.registers[5] = 4000
    vm.exec_dec("R5", 2)
    assert vm.registers[5] == 3998


def test_dec_with_previous_negative_value(vm):
    vm.registers[9] = to_u16(-12)
    vm.exec_dec("R9", 10)
    assert vm.registers[9] == to_u16(-22)


def test_dec_increments_pc(vm):
    vm.exec_dec("R1", 1)
    assert vm.pc == 1


def test_dec_sets_zero_flag(vm):
    vm.registers[7] = 1
    vm.exec_dec("R7", 1)
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_dec_sets_sign_flag(vm):
    vm.registers[1] = 1
    vm.exec_dec("R1", 5)
    assert vm.registers[1] == to_u16(-4)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_dec_sets_carry_flag(vm):
    vm.exec_dec("R8", 1)
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_dec_sets_overflow_flag(vm):
    vm.registers[8] = to_u16(-32768)
    vm.exec_dec("R8", 5)
    assert vm.registers[8] == 32763
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_dec_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[8] = 10
    vm.exec_dec("R8", 5)
    assert vm.registers[8] == 5
    assert not vm.flag_carry


def test_dec_does_not_affect_R0(vm):
    vm.exec_dec("R0", 1)
    assert vm.registers[0] == 0
