import pytest
from unittest.mock import patch

from hera.data import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_lsl(vm):
    with patch("hera.vm.VirtualMachine.exec_lsl") as mock_exec_lsl:
        vm.exec_one(Op("LSL", ["R1", "R2"]))
        assert mock_exec_lsl.call_count == 1
        assert mock_exec_lsl.call_args == (("R1", "R2"), {})


def test_lsl_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == 14


def test_lsl_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == 30000


def test_lsl_with_positive_overflow(vm):
    vm.registers[6] = 17000
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == 34000


def test_lsl_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == to_u16(-14)


def test_lsl_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == to_u16(-16800)


def test_lsl_with_negative_overflow(vm):
    vm.registers[6] = to_u16(-20000)
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == 25536
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_lsl_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = to_u16(-20000)
    vm.flag_carry_block = True
    vm.exec_lsl("R1", "R6")
    assert vm.flag_carry


def test_lsl_shifts_in_carry(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == 15
    assert not vm.flag_carry


def test_lsl_ignores_carry_when_blocked(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == 14
    assert not vm.flag_carry


def test_lsl_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_lsl("R6", "R6")
    assert not vm.flag_carry


def test_lsl_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_lsl("R0", "R6")
    assert vm.registers[0] == 0


def test_lsl_increments_pc(vm):
    vm.exec_lsl("R6", "R6")
    assert vm.pc == 1


def test_lsl_sets_zero_flag(vm):
    vm.registers[6] = 32768
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_lsl_sets_sign_flag(vm):
    vm.registers[6] = 32767
    vm.exec_lsl("R1", "R6")
    assert vm.registers[1] == to_u16(-2)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_lsl_ignores_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_lsl("R1", "R6")
    assert vm.flag_overflow


def test_exec_one_delegates_to_lsr(vm):
    with patch("hera.vm.VirtualMachine.exec_lsr") as mock_exec_lsr:
        vm.exec_one(Op("LSR", ["R1", "R2"]))
        assert mock_exec_lsr.call_count == 1
        assert mock_exec_lsr.call_args == (("R1", "R2"), {})


def test_lsr_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_lsr("R1", "R6")
    assert vm.registers[1] == 3


def test_lsr_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_lsr("R1", "R6")
    assert vm.registers[1] == 7500


def test_lsr_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_lsr("R1", "R6")
    assert vm.registers[1] == 32764


def test_lsr_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_lsr("R1", "R6")
    assert vm.registers[1] == 28568


def test_lsr_with_another_large_nevative(vm):
    vm.registers[6] = to_u16(-20000)
    vm.exec_lsr("R1", "R6")
    assert vm.registers[1] == 22768


def test_lsr_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = 3
    vm.flag_carry_block = True
    vm.exec_lsr("R1", "R6")
    assert vm.registers[1] == 1
    assert vm.flag_carry


def test_lsr_shifts_in_carry(vm):
    vm.registers[6] = 6
    vm.flag_carry = True
    vm.exec_lsr("R1", "R6")
    assert vm.registers[1] == to_u16(-32765)
    assert not vm.flag_carry


def test_lsr_ignores_carry_when_blocked(vm):
    vm.registers[6] = 6
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_lsr("R1", "R6")
    assert vm.registers[1] == 3
    assert not vm.flag_carry


def test_lsr_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_lsr("R6", "R6")
    assert not vm.flag_carry


def test_lsr_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_lsr("R0", "R6")
    assert vm.registers[0] == 0


def test_lsr_increments_pc(vm):
    vm.exec_lsr("R6", "R6")
    assert vm.pc == 1


def test_lsr_sets_zero_flag(vm):
    vm.registers[6] = 1
    vm.exec_lsr("R1", "R6")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_lsr_sets_sign_flag(vm):
    vm.registers[6] = 6
    vm.flag_carry = True
    vm.exec_lsr("R1", "R6")
    assert not vm.flag_zero
    assert vm.flag_sign


def test_lsr_ignores_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_lsr("R1", "R6")
    assert vm.flag_overflow


def test_exec_one_delegates_to_lsl8(vm):
    with patch("hera.vm.VirtualMachine.exec_lsl8") as mock_exec_lsl8:
        vm.exec_one(Op("LSL8", ["R1", "R2"]))
        assert mock_exec_lsl8.call_count == 1
        assert mock_exec_lsl8.call_args == (("R1", "R2"), {})


def test_lsl8_with_small_positive(vm):
    vm.registers[4] = 51
    vm.exec_lsl8("R3", "R4")
    assert vm.registers[3] == 13056


def test_lsl8_with_large_positive(vm):
    vm.registers[4] = 17000
    vm.exec_lsl8("R3", "R4")
    assert vm.registers[3] == 26624


def test_lsl8_with_small_negative(vm):
    vm.registers[4] = -4
    vm.exec_lsl8("R3", "R4")
    assert vm.registers[3] == to_u16(-1024)


def test_lsl8_with_large_negative(vm):
    vm.registers[4] = to_u16(-31781)
    vm.exec_lsl8("R3", "R4")
    assert vm.registers[3] == to_u16(-9472)


def test_lsl8_sets_zero_flag(vm):
    vm.registers[4] = 32768
    vm.exec_lsl8("R3", "R4")
    assert vm.registers[3] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_lsl8_sets_sign_flag(vm):
    vm.registers[4] = 32767
    vm.exec_lsl8("R3", "R4")
    assert vm.registers[3] == to_u16(-256)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_lsl8_increments_pc(vm):
    vm.exec_lsl8("R1", "R1")
    assert vm.pc == 1


def test_lsl8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[4] = 5
    vm.exec_lsl8("R3", "R4")
    assert vm.registers[3] == 1280
    assert vm.flag_carry


def test_lsl8_does_not_set_carry_or_overflow(vm):
    vm.registers[4] = to_u16(-1)
    vm.exec_lsl8("R3", "R4")
    assert vm.registers[3] == to_u16(-256)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_lsl8_does_not_affect_R0(vm):
    vm.registers[4] = 4
    vm.exec_lsl8("R0", "R4")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_lsr8(vm):
    with patch("hera.vm.VirtualMachine.exec_lsr8") as mock_exec_lsr8:
        vm.exec_one(Op("LSR8", ["R1", "R2"]))
        assert mock_exec_lsr8.call_count == 1
        assert mock_exec_lsr8.call_args == (("R1", "R2"), {})


def test_lsr8_with_small_positive(vm):
    vm.registers[4] = 51
    vm.exec_lsr8("R3", "R4")
    assert vm.registers[3] == 0


def test_lsr8_with_large_positive(vm):
    vm.registers[4] = 17000
    vm.exec_lsr8("R3", "R4")
    assert vm.registers[3] == 66


def test_lsr8_with_small_negative(vm):
    vm.registers[4] = to_u16(-4)
    vm.exec_lsr8("R3", "R4")
    assert vm.registers[3] == 255


def test_lsr8_with_large_negative(vm):
    vm.registers[4] = to_u16(-31781)
    vm.exec_lsr8("R3", "R4")
    assert vm.registers[3] == 131


def test_lsr8_sets_zero_flag(vm):
    vm.registers[4] = 17
    vm.exec_lsr8("R3", "R4")
    assert vm.registers[3] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_lsr8_increments_pc(vm):
    vm.exec_lsr8("R1", "R1")
    assert vm.pc == 1


def test_lsr8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[4] = 17000
    vm.exec_lsr8("R3", "R4")
    assert vm.registers[3] == 66
    assert vm.flag_carry


def test_lsr8_does_not_set_carry_or_overflow(vm):
    vm.registers[4] = 15910
    vm.exec_lsr8("R3", "R4")
    assert vm.registers[3] == 62
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_lsr8_does_not_affect_R0(vm):
    vm.registers[4] = 15910
    vm.exec_lsr8("R0", "R4")
    assert vm.registers[0] == 0


def test_exec_one_delegates_to_asl(vm):
    with patch("hera.vm.VirtualMachine.exec_asl") as mock_exec_asl:
        vm.exec_one(Op("ASL", ["R1", "R2"]))
        assert mock_exec_asl.call_count == 1
        assert mock_exec_asl.call_args == (("R1", "R2"), {})


def test_asl_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == 14


def test_asl_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == 30000


def test_asl_with_positive_overflow(vm):
    vm.registers[6] = 17000
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == 34000


def test_asl_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == to_u16(-14)


def test_asl_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == to_u16(-16800)


def test_asl_with_negative_overflow(vm):
    vm.registers[6] = to_u16(-20000)
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == 25536
    assert vm.flag_carry
    assert vm.flag_overflow


def test_asl_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = to_u16(-20000)
    vm.flag_carry_block = True
    vm.exec_asl("R1", "R6")
    assert vm.flag_carry
    assert vm.flag_overflow


def test_asl_shifts_in_carry(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == 15
    assert not vm.flag_carry


def test_asl_ignores_carry_when_blocked(vm):
    vm.registers[6] = 7
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == 14
    assert not vm.flag_carry


def test_asl_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_asl("R6", "R6")
    assert not vm.flag_carry


def test_asl_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_asl("R0", "R6")
    assert vm.registers[0] == 0


def test_asl_increments_pc(vm):
    vm.exec_asl("R6", "R6")
    assert vm.pc == 1


def test_asl_sets_zero_flag(vm):
    vm.registers[6] = 32768
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_asl_sets_sign_flag(vm):
    vm.registers[6] = 32767
    vm.exec_asl("R1", "R6")
    assert vm.registers[1] == to_u16(-2)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_asl_resets_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_asl("R1", "R6")
    assert not vm.flag_overflow


def test_exec_one_delegates_to_asr(vm):
    with patch("hera.vm.VirtualMachine.exec_asr") as mock_exec_asr:
        vm.exec_one(Op("ASR", ["R1", "R2"]))
        assert mock_exec_asr.call_count == 1
        assert mock_exec_asr.call_args == (("R1", "R2"), {})


def test_asr_with_small_positive(vm):
    vm.registers[6] = 7
    vm.exec_asr("R1", "R6")
    assert vm.registers[1] == 3


def test_asr_with_large_positive(vm):
    vm.registers[6] = 15000
    vm.exec_asr("R1", "R6")
    assert vm.registers[1] == 7500


def test_asr_with_small_negative(vm):
    vm.registers[6] = to_u16(-7)
    vm.exec_asr("R1", "R6")
    assert vm.registers[1] == to_u16(-3)


def test_asr_with_another_small_negative(vm):
    vm.registers[6] = to_u16(-5)
    vm.exec_asr("R1", "R6")
    assert vm.registers[1] == to_u16(-2)


def test_asr_with_large_negative(vm):
    vm.registers[6] = to_u16(-8400)
    vm.exec_asr("R1", "R6")
    assert vm.registers[1] == to_u16(-4200)


def test_asr_shifts_out_carry_when_blocked(vm):
    vm.registers[6] = 3
    vm.flag_carry_block = True
    vm.exec_asr("R1", "R6")
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_asr_ignores_incoming_carry(vm):
    vm.registers[6] = 4
    vm.flag_carry = True
    vm.exec_asr("R1", "R6")
    assert vm.registers[1] == 2
    assert not vm.flag_carry


def test_asr_ignores_carry_when_blocked(vm):
    vm.registers[6] = 4
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_asr("R1", "R6")
    assert vm.registers[1] == 2
    assert not vm.flag_carry


def test_asr_resets_carry(vm):
    vm.flag_carry = True
    vm.exec_asr("R6", "R6")
    assert not vm.flag_carry


def test_asr_does_not_affect_R0(vm):
    vm.registers[6] = 7
    vm.exec_asr("R0", "R6")
    assert vm.registers[0] == 0


def test_asr_increments_pc(vm):
    vm.exec_asr("R6", "R6")
    assert vm.pc == 1


def test_asr_sets_zero_flag(vm):
    vm.registers[6] = 1
    vm.exec_asr("R1", "R6")
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_asr_sets_sign_flag(vm):
    vm.registers[6] = to_u16(-20)
    vm.exec_asr("R1", "R6")
    assert vm.registers[1] == to_u16(-10)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_asr_does_not_reset_overflow_flag(vm):
    vm.flag_overflow = True
    vm.exec_asr("R1", "R6")
    assert vm.flag_overflow
