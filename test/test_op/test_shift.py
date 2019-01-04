import pytest
from unittest.mock import patch

from hera.data import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_LSL(vm):
    with patch("hera.vm.VirtualMachine.exec_LSL") as mock_exec_LSL:
        vm.exec_one(Op("LSL", ["R1", "R2"]))
        assert mock_exec_LSL.call_count == 1
        assert mock_exec_LSL.call_args == (("R1", "R2"), {})


def test_LSL_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == 14


def test_LSL_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == 30000


def test_LSL_with_positive_overflow(vm):
    vm.registers[6] = 17000
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == 34000


def test_LSL_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == to_u16(-14)


def test_LSL_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == to_u16(-16800)


def test_LSL_with_negative_overflow(vm):
    vm.registers[6] = to_u16(-20000)
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == 25536
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_LSL_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = to_u16(-20000)
    vm.flag_carry_block = True
    vm.exec_LSL("R1", "R6")
    assert vm.flag_carry


def test_LSL_shifts_in_carry(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == 15
    assert not vm.flag_carry


def test_LSL_ignores_carry_when_blocked(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == 14
    assert not vm.flag_carry


def test_LSL_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_LSL("R6", "R6")
    assert not vm.flag_carry


def test_LSL_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_LSL("R0", "R6")
    assert vm.registers[0] == 0


def test_LSL_increments_pc(vm):
    vm.exec_LSL("R6", "R6")
    assert vm.pc == 1


def test_LSL_sets_zero_flag(vm):
    vm.registers[6] = 32768
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_LSL_sets_sign_flag(vm):
    vm.registers[6] = 32767
    vm.exec_LSL("R1", "R6")
    assert vm.registers[1] == to_u16(-2)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_LSL_ignores_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_LSL("R1", "R6")
    assert vm.flag_overflow


def test_exec_one_delegates_to_LSR(vm):
    with patch("hera.vm.VirtualMachine.exec_LSR") as mock_exec_LSR:
        vm.exec_one(Op("LSR", ["R1", "R2"]))
        assert mock_exec_LSR.call_count == 1
        assert mock_exec_LSR.call_args == (("R1", "R2"), {})


def test_LSR_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_LSR("R1", "R6")
    assert vm.registers[1] == 3


def test_LSR_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_LSR("R1", "R6")
    assert vm.registers[1] == 7500


def test_LSR_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_LSR("R1", "R6")
    assert vm.registers[1] == 32764


def test_LSR_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_LSR("R1", "R6")
    assert vm.registers[1] == 28568


def test_LSR_with_another_large_nevative(vm):
    vm.registers[6] = to_u16(-20000)
    vm.exec_LSR("R1", "R6")
    assert vm.registers[1] == 22768


def test_LSR_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = 3
    vm.flag_carry_block = True
    vm.exec_LSR("R1", "R6")
    assert vm.registers[1] == 1
    assert vm.flag_carry


def test_LSR_shifts_in_carry(vm):
    vm.registers[6] = 6
    vm.flag_carry = True
    vm.exec_LSR("R1", "R6")
    assert vm.registers[1] == to_u16(-32765)
    assert not vm.flag_carry


def test_LSR_ignores_carry_when_blocked(vm):
    vm.registers[6] = 6
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_LSR("R1", "R6")
    assert vm.registers[1] == 3
    assert not vm.flag_carry


def test_LSR_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_LSR("R6", "R6")
    assert not vm.flag_carry


def test_LSR_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_LSR("R0", "R6")
    assert vm.registers[0] == 0


def test_LSR_increments_pc(vm):
    vm.exec_LSR("R6", "R6")
    assert vm.pc == 1


def test_LSR_sets_zero_flag(vm):
    vm.registers[6] = 1
    vm.exec_LSR("R1", "R6")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_LSR_sets_sign_flag(vm):
    vm.registers[6] = 6
    vm.flag_carry = True
    vm.exec_LSR("R1", "R6")
    assert not vm.flag_zero
    assert vm.flag_sign


def test_LSR_ignores_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_LSR("R1", "R6")
    assert vm.flag_overflow


def test_exec_one_delegates_to_LSL8(vm):
    with patch("hera.vm.VirtualMachine.exec_LSL8") as mock_exec_LSL8:
        vm.exec_one(Op("LSL8", ["R1", "R2"]))
        assert mock_exec_LSL8.call_count == 1
        assert mock_exec_LSL8.call_args == (("R1", "R2"), {})


def test_LSL8_with_small_positive(vm):
    vm.registers[4] = 51
    vm.exec_LSL8("R3", "R4")
    assert vm.registers[3] == 13056


def test_LSL8_with_large_positive(vm):
    vm.registers[4] = 17000
    vm.exec_LSL8("R3", "R4")
    assert vm.registers[3] == 26624


def test_LSL8_with_small_negative(vm):
    vm.registers[4] = -4
    vm.exec_LSL8("R3", "R4")
    assert vm.registers[3] == to_u16(-1024)


def test_LSL8_with_large_negative(vm):
    vm.registers[4] = to_u16(-31781)
    vm.exec_LSL8("R3", "R4")
    assert vm.registers[3] == to_u16(-9472)


def test_LSL8_sets_zero_flag(vm):
    vm.registers[4] = 32768
    vm.exec_LSL8("R3", "R4")
    assert vm.registers[3] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_LSL8_sets_sign_flag(vm):
    vm.registers[4] = 32767
    vm.exec_LSL8("R3", "R4")
    assert vm.registers[3] == to_u16(-256)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_LSL8_increments_pc(vm):
    vm.exec_LSL8("R1", "R1")
    assert vm.pc == 1


def test_LSL8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[4] = 5
    vm.exec_LSL8("R3", "R4")
    assert vm.registers[3] == 1280
    assert vm.flag_carry


def test_LSL8_does_not_set_carry_or_overflow(vm):
    vm.registers[4] = to_u16(-1)
    vm.exec_LSL8("R3", "R4")
    assert vm.registers[3] == to_u16(-256)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_LSL8_does_not_affect_R0(vm):
    vm.registers[4] = 4
    vm.exec_LSL8("R0", "R4")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_LSR8(vm):
    with patch("hera.vm.VirtualMachine.exec_LSR8") as mock_exec_LSR8:
        vm.exec_one(Op("LSR8", ["R1", "R2"]))
        assert mock_exec_LSR8.call_count == 1
        assert mock_exec_LSR8.call_args == (("R1", "R2"), {})


def test_LSR8_with_small_positive(vm):
    vm.registers[4] = 51
    vm.exec_LSR8("R3", "R4")
    assert vm.registers[3] == 0


def test_LSR8_with_large_positive(vm):
    vm.registers[4] = 17000
    vm.exec_LSR8("R3", "R4")
    assert vm.registers[3] == 66


def test_LSR8_with_small_negative(vm):
    vm.registers[4] = to_u16(-4)
    vm.exec_LSR8("R3", "R4")
    assert vm.registers[3] == 255


def test_LSR8_with_large_negative(vm):
    vm.registers[4] = to_u16(-31781)
    vm.exec_LSR8("R3", "R4")
    assert vm.registers[3] == 131


def test_LSR8_sets_zero_flag(vm):
    vm.registers[4] = 17
    vm.exec_LSR8("R3", "R4")
    assert vm.registers[3] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_LSR8_increments_pc(vm):
    vm.exec_LSR8("R1", "R1")
    assert vm.pc == 1


def test_LSR8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[4] = 17000
    vm.exec_LSR8("R3", "R4")
    assert vm.registers[3] == 66
    assert vm.flag_carry


def test_LSR8_does_not_set_carry_or_overflow(vm):
    vm.registers[4] = 15910
    vm.exec_LSR8("R3", "R4")
    assert vm.registers[3] == 62
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_LSR8_does_not_affect_R0(vm):
    vm.registers[4] = 15910
    vm.exec_LSR8("R0", "R4")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_ASL(vm):
    with patch("hera.vm.VirtualMachine.exec_ASL") as mock_exec_ASL:
        vm.exec_one(Op("ASL", ["R1", "R2"]))
        assert mock_exec_ASL.call_count == 1
        assert mock_exec_ASL.call_args == (("R1", "R2"), {})


def test_ASL_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == 14


def test_ASL_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == 30000


def test_ASL_with_positive_overflow(vm):
    vm.registers[6] = 17000
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == 34000


def test_ASL_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == to_u16(-14)


def test_ASL_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == to_u16(-16800)


def test_ASL_with_negative_overflow(vm):
    vm.registers[6] = to_u16(-20000)
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == 25536
    assert vm.flag_carry
    assert vm.flag_overflow


def test_ASL_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = to_u16(-20000)
    vm.flag_carry_block = True
    vm.exec_ASL("R1", "R6")
    assert vm.flag_carry
    assert vm.flag_overflow


def test_ASL_shifts_in_carry(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == 15
    assert not vm.flag_carry


def test_ASL_ignores_carry_when_blocked(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == 14
    assert not vm.flag_carry


def test_ASL_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_ASL("R6", "R6")
    assert not vm.flag_carry


def test_ASL_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_ASL("R0", "R6")
    assert vm.registers[0] == 0


def test_ASL_increments_pc(vm):
    vm.exec_ASL("R6", "R6")
    assert vm.pc == 1


def test_ASL_sets_zero_flag(vm):
    vm.registers[6] = 32768
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_ASL_sets_sign_flag(vm):
    vm.registers[6] = 32767
    vm.exec_ASL("R1", "R6")
    assert vm.registers[1] == to_u16(-2)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_ASL_resets_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_ASL("R1", "R6")
    assert not vm.flag_overflow


def test_exec_one_delegates_to_ASR(vm):
    with patch("hera.vm.VirtualMachine.exec_ASR") as mock_exec_ASR:
        vm.exec_one(Op("ASR", ["R1", "R2"]))
        assert mock_exec_ASR.call_count == 1
        assert mock_exec_ASR.call_args == (("R1", "R2"), {})


def test_ASR_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_ASR("R1", "R6")
    assert vm.registers[1] == 3


def test_ASR_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_ASR("R1", "R6")
    assert vm.registers[1] == 7500


def test_ASR_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_ASR("R1", "R6")
    assert vm.registers[1] == to_u16(-3)


def test_ASR_with_another_small_negative(vm):
    vm.registers[6] = to_u16(-5)
    vm.exec_ASR("R1", "R6")
    assert vm.registers[1] == to_u16(-2)


def test_ASR_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_ASR("R1", "R6")
    assert vm.registers[1] == to_u16(-4200)


def test_ASR_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = 3
    vm.flag_carry_block = True
    vm.exec_ASR("R1", "R6")
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_ASR_ignores_incoming_carry(vm):
    vm.registers[6] = 4
    vm.flag_carry = True
    vm.exec_ASR("R1", "R6")
    assert vm.registers[1] == 2
    assert not vm.flag_carry


def test_ASR_ignores_carry_when_blocked(vm):
    vm.registers[6] = 4
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_ASR("R1", "R6")
    assert vm.registers[1] == 2
    assert not vm.flag_carry


def test_ASR_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_ASR("R6", "R6")
    assert not vm.flag_carry


def test_ASR_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_ASR("R0", "R6")
    assert vm.registers[0] == 0


def test_ASR_increments_pc(vm):
    vm.exec_ASR("R6", "R6")
    assert vm.pc == 1


def test_ASR_sets_zero_flag(vm):
    vm.registers[6] = 1
    vm.exec_ASR("R1", "R6")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_ASR_sets_sign_flag(vm):
    vm.registers[6] = to_u16(-20)
    vm.exec_ASR("R1", "R6")
    assert vm.registers[1] == to_u16(-10)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_ASR_does_not_reset_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_ASR("R1", "R6")
    assert vm.flag_overflow
