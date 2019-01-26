import pytest
from .utils import helper

from hera.data import Op
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_calculate_LSL_with_small_positive(vm):
    vm.registers[2] = 7

    helper(vm, "LSL(R1, R2)")

    assert vm.registers[1] == 14


def test_LSL_with_large_positive(vm):
    vm.registers[2] = 15000

    helper(vm, "LSL(R1, R2)")

    assert vm.registers[1] == 30000


def test_LSL_with_positive_overflow(vm):
    vm.registers[2] = 17000

    helper(vm, "LSL(R1, R2)")

    assert vm.registers[1] == 34000


def test_LSL_with_small_negative(vm):
    vm.registers[2] = to_u16(-7)

    helper(vm, "LSL(R1, R2)")

    assert vm.registers[1] == to_u16(-14)
    assert vm.flag_sign
    assert not vm.flag_zero


def test_LSL_with_large_negative(vm):
    vm.registers[2] = to_u16(-8400)

    helper(vm, "LSL(R1, R2)")

    assert vm.registers[1] == to_u16(-16800)


def test_LSL_with_negative_overflow(vm):
    vm.registers[2] = to_u16(-20000)

    helper(vm, "LSL(R1, R2)")

    assert vm.registers[1] == 25536
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_LSL_shifts_out_carry_when_blocked(vm):
    vm.flag_carry_block = True
    vm.registers[2] = to_u16(-20000)

    helper(vm, "LSL(R1, R2)")

    assert vm.flag_carry


def test_LSL_shifts_in_carry(vm):
    vm.flag_carry = True
    vm.registers[2] = 7

    helper(vm, "LSL(R1, R2)")

    assert vm.registers[1] == 15
    assert not vm.flag_carry


def test_LSL_ignores_carry_when_blocked(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.registers[2] = 7

    helper(vm, "LSL(R1, R2)")

    assert vm.registers[1] == 14
    assert not vm.flag_carry


def test_LSL_resets_carry(vm):
    vm.flag_carry = True

    helper(vm, "LSL(R1, R2)")

    assert not vm.flag_carry


def test_LSL_ignores_overflow_flag(vm):
    vm.flag_overflow = True

    helper(vm, "LSL(R1, R2)")

    assert vm.flag_overflow


def test_LSR_with_small_positive(vm):
    vm.registers[2] = 7

    helper(vm, "LSR(R1, R2)")

    assert vm.registers[1] == 3


def test_LSR_with_large_positive(vm):
    vm.registers[2] = 15000

    helper(vm, "LSR(R1, R2)")

    assert vm.registers[1] == 7500


def test_LSR_with_small_negative(vm):
    vm.registers[2] = to_u16(-7)

    helper(vm, "LSR(R1, R2)")

    assert vm.registers[1] == 32764


def test_LSR_with_large_negative(vm):
    vm.registers[2] = to_u16(-8400)

    helper(vm, "LSR(R1, R2)")

    assert vm.registers[1] == 28568


def test_LSR_with_another_large_negative(vm):
    vm.registers[2] = to_u16(-20000)

    helper(vm, "LSR(R1, R2)")

    assert vm.registers[1] == 22768


def test_LSR_shifts_out_carry_when_blocked(vm):
    vm.flag_carry_block = True
    vm.registers[2] = 3

    helper(vm, "LSR(R1, R2)")

    assert vm.registers[1] == 1
    assert vm.flag_carry


def test_LSR_shifts_in_carry(vm):
    vm.flag_carry = True
    vm.registers[2] = 6

    helper(vm, "LSR(R1, R2)")

    assert vm.registers[1] == to_u16(-32765)
    assert not vm.flag_carry


def test_LSR_ignores_carry_when_blocked(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.registers[2] = 6

    helper(vm, "LSR(R1, R2)")

    assert vm.registers[1] == 3
    assert not vm.flag_carry


def test_LSR_resets_carry(vm):
    vm.flag_carry = True

    helper(vm, "LSR(R1, R2)")

    assert not vm.flag_carry


def test_LSR_ignores_overflow_flag(vm):
    vm.flag_overflow = True

    helper(vm, "LSR(R1, R2)")

    assert vm.flag_overflow


def test_LSL8_with_small_positive(vm):
    vm.registers[2] = 51

    helper(vm, "LSL8(R1, R2)")

    assert vm.registers[1] == 13056


def test_LSL8_with_large_positive(vm):
    vm.registers[2] = 17000

    helper(vm, "LSL8(R1, R2)")

    assert vm.registers[1] == 26624


def test_LSL8_with_small_negative(vm):
    vm.registers[2] = to_u16(-4)

    helper(vm, "LSL8(R1, R2)")

    assert vm.registers[1] == to_u16(-1024)


def test_LSL8_with_large_negative(vm):
    vm.registers[2] = to_u16(-31781)

    helper(vm, "LSL8(R1, R2)")

    assert vm.registers[1] == to_u16(-9472)


def test_LSL8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[2] = 5

    helper(vm, "LSL8(R1, R2)")

    assert vm.registers[1] == 1280
    assert vm.flag_carry


def test_LSL8_does_not_set_carry_or_overflow(vm):
    vm.registers[2] = to_u16(-1)

    helper(vm, "LSL8(R1, R2)")

    assert vm.registers[1] == to_u16(-256)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_LSR8_with_small_positive(vm):
    vm.registers[2] = 51

    helper(vm, "LSR8(R1, R2)")

    assert vm.registers[1] == 0
    assert not vm.flag_sign
    assert vm.flag_zero


def test_LSR8_with_large_positive(vm):
    vm.registers[2] = 17000

    helper(vm, "LSR8(R1, R2)")

    assert vm.calculate_LSR8(17000) == 66


def test_LSR8_with_small_negative(vm):
    vm.registers[2] = to_u16(-4)

    helper(vm, "LSR8(R1, R2)")

    assert vm.registers[1] == 255


def test_LSR8_with_large_negative(vm):
    vm.registers[2] = to_u16(-31781)

    helper(vm, "LSR8(R1, R2)")

    assert vm.registers[1] == 131


def test_LSR8_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[2] = 17000

    helper(vm, "LSR8(R1, R2)")

    assert vm.registers[1] == 66
    assert vm.flag_carry


def test_LSR8_does_not_set_carry_or_overflow(vm):
    vm.registers[2] = 15910

    helper(vm, "LSR8(R1, R2)")

    assert vm.registers[1] == 62
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_ASL_with_small_positive(vm):
    vm.registers[2] = 7

    helper(vm, "ASL(R1, R2)")

    assert vm.registers[1] == 14


def test_ASL_with_large_positive(vm):
    vm.registers[2] = 15000

    helper(vm, "ASL(R1, R2)")

    assert vm.registers[1] == 30000


def test_ASL_with_positive_overflow(vm):
    vm.registers[2] = 17000

    helper(vm, "ASL(R1, R2)")

    assert vm.registers[1] == 34000


def test_ASL_with_small_negative(vm):
    vm.registers[2] = to_u16(-7)

    helper(vm, "ASL(R1, R2)")

    assert vm.registers[1] == to_u16(-14)


def test_ASL_with_large_negative(vm):
    vm.registers[2] = to_u16(-8400)

    helper(vm, "ASL(R1, R2)")

    assert vm.registers[1] == to_u16(-16800)


def test_ASL_with_negative_overflow(vm):
    vm.registers[2] = to_u16(-20000)

    helper(vm, "ASL(R1, R2)")

    assert vm.registers[1] == 25536
    assert vm.flag_carry
    assert vm.flag_overflow


def test_ASL_shifts_out_carry_when_blocked(vm):
    vm.registers[2] = to_u16(-20000)

    helper(vm, "ASL(R1, R2)")

    assert vm.flag_carry
    assert vm.flag_overflow


def test_ASL_shifts_in_carry(vm):
    vm.flag_carry = True
    vm.registers[2] = 7

    helper(vm, "ASL(R1, R2)")

    assert vm.registers[1] == 15
    assert not vm.flag_carry


def test_ASL_ignores_carry_when_blocked(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.registers[2] = 7

    helper(vm, "ASL(R1, R2)")

    assert vm.registers[1] == 14
    assert not vm.flag_carry


def test_ASL_resets_carry(vm):
    vm.flag_carry = True

    helper(vm, "ASL(R1, R2)")

    assert not vm.flag_carry


def test_ASL_resets_overflow_flag(vm):
    vm.flag_overflow = True

    helper(vm, "ASL(R1, R2)")

    assert not vm.flag_overflow


def test_ASR_with_small_positive(vm):
    vm.registers[2] = 7

    helper(vm, "ASR(R1, R2)")

    assert vm.registers[1] == 3


def test_ASR_with_large_positive(vm):
    vm.registers[2] = 15000

    helper(vm, "ASR(R1, R2)")

    assert vm.registers[1] == 7500


def test_ASR_with_small_negative(vm):
    vm.registers[2] = to_u16(-7)

    helper(vm, "ASR(R1, R2)")

    assert vm.registers[1] == to_u16(-3)


def test_ASR_with_another_small_negative(vm):
    vm.registers[2] = to_u16(-5)

    helper(vm, "ASR(R1, R2)")

    assert vm.registers[1] == to_u16(-2)


def test_ASR_with_large_negative(vm):
    vm.registers[2] = to_u16(-8400)

    helper(vm, "ASR(R1, R2)")

    assert vm.registers[1] == to_u16(-4200)


def test_ASR_shifts_out_carry_when_blocked(vm):
    vm.flag_carry_block = True
    vm.registers[2] = 3

    helper(vm, "ASR(R1, R2)")

    assert vm.flag_carry
    assert not vm.flag_overflow


def test_ASR_ignores_incoming_carry(vm):
    vm.flag_carry = True
    vm.registers[2] = 4

    helper(vm, "ASR(R1, R2)")

    assert vm.registers[1] == 2
    assert not vm.flag_carry


def test_ASR_ignores_carry_when_blocked(vm):
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.registers[2] = 4

    helper(vm, "ASR(R1, R2)")

    assert vm.registers[1] == 2
    assert not vm.flag_carry


def test_ASR_resets_carry(vm):
    vm.flag_carry = True

    helper(vm, "ASR(R1, R2)")

    assert not vm.flag_carry


def test_ASR_does_not_reset_overflow_flag(vm):
    vm.flag_overflow = True

    helper(vm, "ASR(R1, R2)")

    assert vm.flag_overflow
