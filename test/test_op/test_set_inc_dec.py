import pytest
from unittest.mock import patch

from hera.data import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_SETLO(vm):
    with patch("hera.vm.VirtualMachine.exec_SETLO") as mock_exec_SETLO:
        vm.exec_one(Op("SETLO", ["R1", 47]))
        assert mock_exec_SETLO.call_count == 1
        assert mock_exec_SETLO.call_args == (("R1", 47), {})


def test_SETLO_with_positive(vm):
    vm.exec_SETLO("R5", 23)
    assert vm.registers[5] == 23


def test_SETLO_with_negative(vm):
    vm.exec_SETLO("R9", -12)
    assert vm.registers[9] == to_u16(-12)


def test_SETLO_with_max_positive(vm):
    vm.exec_SETLO("R2", 127)
    assert vm.registers[2] == 127


def test_SETLO_with_255(vm):
    vm.exec_SETLO("R2", 255)
    assert vm.registers[2] == to_u16(-1)


def test_SETLO_with_max_negative(vm):
    vm.exec_SETLO("R2", -128)
    assert vm.registers[2] == to_u16(-128)


def test_SETLO_clears_high_bits(vm):
    vm.registers[6] = 4765
    vm.exec_SETLO("R6", 68)
    assert vm.registers[6] == 68


def test_SETLO_increments_pc(vm):
    vm.exec_SETLO("R9", -12)
    assert vm.pc == 1


def test_SETLO_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False
    vm.exec_SETLO("R7", 0)
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_SETLO_does_not_set_zero_flag(vm):
    vm.exec_SETLO("R7", 0)
    assert not vm.flag_zero


def test_SETLO_does_not_set_sign_flag(vm):
    vm.exec_SETLO("R7", -1)
    assert not vm.flag_sign


def test_SETLO_does_not_change_R0(vm):
    vm.exec_SETLO("R0", 20)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_SETHI(vm):
    with patch("hera.vm.VirtualMachine.exec_SETHI") as mock_exec_SETHI:
        vm.exec_one(Op("SETHI", ["R1", 47]))
        assert mock_exec_SETHI.call_count == 1
        assert mock_exec_SETHI.call_args == (("R1", 47), {})


def test_SETHI_with_positive(vm):
    vm.exec_SETHI("R5", 23)
    assert vm.registers[5] == 5888


def test_SETHI_with_max_positive(vm):
    vm.exec_SETHI("R2", 255)
    assert vm.registers[2] == 65280


def test_SETHI_does_not_clear_low_bits(vm):
    vm.registers[6] = 4765
    vm.exec_SETHI("R6", 68)
    assert vm.registers[6] == 17565


def test_SETHI_increments_pc(vm):
    vm.exec_SETHI("R9", 12)
    assert vm.pc == 1


def test_SETHI_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False
    vm.exec_SETHI("R7", 0)
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_SETHI_does_not_set_zero_flag(vm):
    vm.exec_SETHI("R7", 0)
    assert not vm.flag_zero


def test_SETHI_does_not_set_sign_flag(vm):
    vm.exec_SETHI("R7", -1)
    assert not vm.flag_sign


def test_SETHI_does_not_change_R0(vm):
    vm.exec_SETHI("R0", 20)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_INC(vm):
    with patch("hera.vm.VirtualMachine.exec_INC") as mock_exec_INC:
        vm.exec_one(Op("INC", ["R1", 1]))
        assert mock_exec_INC.call_count == 1
        assert mock_exec_INC.call_args == (("R1", 1), {})


def test_INC_with_small_positive(vm):
    vm.exec_INC("R8", 6)
    assert vm.registers[8] == 6


def test_INC_with_max(vm):
    vm.exec_INC("R2", 32)
    assert vm.registers[2] == 32


def test_INC_with_previous_value(vm):
    vm.registers[5] = 4000
    vm.exec_INC("R5", 2)
    assert vm.registers[5] == 4002


def test_INC_with_previous_negative_value(vm):
    vm.registers[9] = to_u16(-12)
    vm.exec_INC("R9", 10)
    assert vm.registers[9] == to_u16(-2)


def test_INC_increments_pc(vm):
    vm.exec_INC("R1", 1)
    assert vm.pc == 1


def test_INC_sets_zero_flag(vm):
    vm.registers[7] = to_u16(-1)
    vm.exec_INC("R7", 1)
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_INC_sets_sign_flag(vm):
    vm.registers[1] = 32765
    vm.exec_INC("R1", 5)
    assert vm.registers[1] == to_u16(-32766)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_INC_sets_carry_flag(vm):
    vm.registers[8] = to_u16(-1)
    vm.exec_INC("R8", 1)
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_INC_sets_overflow_flag(vm):
    vm.registers[8] = 32765
    vm.exec_INC("R8", 5)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_INC_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.exec_INC("R8", 5)
    assert vm.registers[8] == 5
    assert not vm.flag_carry


def test_INC_does_not_affect_R0(vm):
    vm.exec_INC("R0", 1)
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_DEC(vm):
    with patch("hera.vm.VirtualMachine.exec_DEC") as mock_exec_DEC:
        vm.exec_one(Op("DEC", ["R1", 1]))
        assert mock_exec_DEC.call_count == 1
        assert mock_exec_DEC.call_args == (("R1", 1), {})


def test_DEC_with_small_positive(vm):
    vm.exec_DEC("R8", 6)
    assert vm.registers[8] == to_u16(-6)


def test_DEC_with_max(vm):
    vm.exec_DEC("R2", 32)
    assert vm.registers[2] == to_u16(-32)


def test_DEC_with_previous_value(vm):
    vm.registers[5] = 4000
    vm.exec_DEC("R5", 2)
    assert vm.registers[5] == 3998


def test_DEC_with_previous_negative_value(vm):
    vm.registers[9] = to_u16(-12)
    vm.exec_DEC("R9", 10)
    assert vm.registers[9] == to_u16(-22)


def test_DEC_increments_pc(vm):
    vm.exec_DEC("R1", 1)
    assert vm.pc == 1


def test_DEC_sets_zero_flag(vm):
    vm.registers[7] = 1
    vm.exec_DEC("R7", 1)
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_DEC_sets_sign_flag(vm):
    vm.registers[1] = 1
    vm.exec_DEC("R1", 5)
    assert vm.registers[1] == to_u16(-4)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_DEC_sets_carry_flag(vm):
    vm.exec_DEC("R8", 1)
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_DEC_sets_overflow_flag(vm):
    vm.registers[8] = to_u16(-32768)
    vm.exec_DEC("R8", 5)
    assert vm.registers[8] == 32763
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_DEC_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[8] = 10
    vm.exec_DEC("R8", 5)
    assert vm.registers[8] == 5
    assert not vm.flag_carry


def test_DEC_does_not_affect_R0(vm):
    vm.exec_DEC("R0", 1)
    assert vm.registers[0] == 0
