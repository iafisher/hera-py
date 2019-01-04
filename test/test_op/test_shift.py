import pytest

from hera.data import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_aslu_op_with_LSL(vm):
    vm.registers[2] = 40

    vm.exec_one(Op("LSL", ["R1", "R2"]))

    assert vm.pc == 1
    assert vm.registers[1] == 80
    assert not vm.flag_sign
    assert not vm.flag_zero


def test_calculate_LSL_with_small_positive(vm):
    assert vm.calculate_LSL(7) == 14


def test_LSL_with_large_positive(vm):
    assert vm.calculate_LSL(15000) == 30000


def test_LSL_with_positive_overflow(vm):
    assert vm.calculate_LSL(17000) == 34000


def test_LSL_with_small_negative(vm):
    assert vm.calculate_LSL(to_u16(-7)) == to_u16(-14)


def test_LSL_with_large_negative(vm):
    assert vm.calculate_LSL(to_u16(-8400)) == to_u16(-16800)


def test_LSL_with_negative_overflow(vm):
    assert vm.calculate_LSL(to_u16(-20000)) == 25536
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_LSL_shifts_out_carry_when_blocked(vm):
    vm.flag_carry_block = True
    vm.calculate_LSL(to_u16(-20000))
    assert vm.flag_carry


def test_LSL_shifts_in_carry(vm):
    vm.flag_carry = True
    assert vm.calculate_LSL(7) == 15
    assert not vm.flag_carry


def test_LSL_ignores_carry_when_blocked(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    assert vm.calculate_LSL(7) == 14
    assert not vm.flag_carry


def test_LSL_resets_carry(vm):
    vm.flag_carry = True
    vm.calculate_LSL(0)
    assert not vm.flag_carry


def test_LSL_ignores_overflow_flag(vm):
    vm.flag_overflow = True
    vm.calculate_LSL(0)
    assert vm.flag_overflow


def test_LSR_with_small_positive(vm):
    assert vm.calculate_LSR(7) == 3


def test_LSR_with_large_positive(vm):
    assert vm.calculate_LSR(15000) == 7500


def test_LSR_with_small_negative(vm):
    assert vm.calculate_LSR(to_u16(-7)) == 32764


def test_LSR_with_large_negative(vm):
    assert vm.calculate_LSR(to_u16(-8400)) == 28568


def test_LSR_with_another_large_negative(vm):
    assert vm.calculate_LSR(to_u16(-20000)) == 22768


def test_LSR_shifts_out_carry_when_blocked(vm):
    vm.flag_carry_block = True
    assert vm.calculate_LSR(3) == 1
    assert vm.flag_carry


def test_LSR_shifts_in_carry(vm):
    vm.flag_carry = True
    assert vm.calculate_LSR(6) == to_u16(-32765)
    assert not vm.flag_carry


def test_LSR_ignores_carry_when_blocked(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    assert vm.calculate_LSR(6) == 3
    assert not vm.flag_carry


def test_LSR_resets_carry(vm):
    vm.flag_carry = True
    vm.calculate_LSR(0)
    assert not vm.flag_carry


def test_LSR_ignores_overflow_flag(vm):
    vm.flag_overflow = True
    vm.calculate_LSR(0)
    assert vm.flag_overflow


def test_LSL8_with_small_positive(vm):
    assert vm.calculate_LSL8(51) == 13056


def test_LSL8_with_large_positive(vm):
    assert vm.calculate_LSL8(17000) == 26624


def test_LSL8_with_small_negative(vm):
    assert vm.calculate_LSL8(to_u16(-4)) == to_u16(-1024)


def test_LSL8_with_large_negative(vm):
    assert vm.calculate_LSL8(to_u16(-31781)) == to_u16(-9472)


def test_LSL8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    assert vm.calculate_LSL8(5) == 1280
    assert vm.flag_carry


def test_LSL8_does_not_set_carry_or_overflow(vm):
    assert vm.calculate_LSL8(to_u16(-1)) == to_u16(-256)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_LSR8_with_small_positive(vm):
    assert vm.calculate_LSR8(51) == 0


def test_LSR8_with_large_positive(vm):
    assert vm.calculate_LSR8(17000) == 66


def test_LSR8_with_small_negative(vm):
    assert vm.calculate_LSR8(to_u16(-4)) == 255


def test_LSR8_with_large_negative(vm):
    assert vm.calculate_LSR8(to_u16(-31781)) == 131


def test_LSR8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    assert vm.calculate_LSR8(17000) == 66
    assert vm.flag_carry


def test_LSR8_does_not_set_carry_or_overflow(vm):
    assert vm.calculate_LSR8(15910) == 62
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_ASL_with_small_positive(vm):
    assert vm.calculate_ASL(7) == 14


def test_ASL_with_large_positive(vm):
    assert vm.calculate_ASL(15000) == 30000


def test_ASL_with_positive_overflow(vm):
    assert vm.calculate_ASL(17000) == 34000


def test_ASL_with_small_negative(vm):
    assert vm.calculate_ASL(to_u16(-7)) == to_u16(-14)


def test_ASL_with_large_negative(vm):
    assert vm.calculate_ASL(to_u16(-8400)) == to_u16(-16800)


def test_ASL_with_negative_overflow(vm):
    assert vm.calculate_ASL(to_u16(-20000)) == 25536
    assert vm.flag_carry
    assert vm.flag_overflow


def test_ASL_shifts_out_carry_when_blocked(vm):
    vm.calculate_ASL(to_u16(-20000))
    assert vm.flag_carry
    assert vm.flag_overflow


def test_ASL_shifts_in_carry(vm):
    vm.flag_carry = True
    assert vm.calculate_ASL(7) == 15
    assert not vm.flag_carry


def test_ASL_ignores_carry_when_blocked(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    assert vm.calculate_ASL(7) == 14
    assert not vm.flag_carry


def test_ASL_resets_carry(vm):
    vm.flag_carry = True
    vm.calculate_ASL(0)
    assert not vm.flag_carry


def test_ASL_resets_overflow_flag(vm):
    vm.flag_overflow = True
    vm.calculate_ASL(0)
    assert not vm.flag_overflow


def test_ASR_with_small_positive(vm):
    assert vm.calculate_ASR(7) == 3


def test_ASR_with_large_positive(vm):
    assert vm.calculate_ASR(15000) == 7500


def test_ASR_with_small_negative(vm):
    assert vm.calculate_ASR(to_u16(-7)) == to_u16(-3)


def test_ASR_with_another_small_negative(vm):
    assert vm.calculate_ASR(to_u16(-5)) == to_u16(-2)


def test_ASR_with_large_negative(vm):
    assert vm.calculate_ASR(to_u16(-8400)) == to_u16(-4200)


def test_ASR_shifts_out_carry_when_blocked(vm):
    vm.flag_carry_block = True
    vm.calculate_ASR(3)
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_ASR_ignores_incoming_carry(vm):
    vm.flag_carry = True
    assert vm.calculate_ASR(4) == 2
    assert not vm.flag_carry


def test_ASR_ignores_carry_when_blocked(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    assert vm.calculate_ASR(4) == 2
    assert not vm.flag_carry


def test_ASR_resets_carry(vm):
    vm.flag_carry = True
    vm.calculate_ASR(0)
    assert not vm.flag_carry


def test_ASR_does_not_reset_overflow_flag(vm):
    vm.flag_overflow = True
    vm.calculate_ASR(0)
    assert vm.flag_overflow
