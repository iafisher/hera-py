import pytest

from lark import Token

from hera.op import Set, Sethi, Setlo
from hera.utils import HERAError, to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def REG(s):
    return Token("REGISTER", s)


def test_SET_convert_with_small_positive():
    inst = Set("R1", 3)
    assert inst.convert() == [Setlo("R1", 3)]


def test_SET_convert_with_large_positive():
    inst = Set("R1", 34000)
    assert inst.convert() == [Setlo("R1", 208), Sethi("R1", 132)]


def test_SET_convert_with_negative():
    inst = Set("R1", -5)
    assert inst.convert() == [Setlo("R1", 251), Sethi("R1", 255)]


def test_SET_convert_with_symbol():
    inst = Set("R1", "whatever")
    assert inst.convert() == [Setlo("R1", "whatever"), Sethi("R1", "whatever")]


def test_SET_verify_with_too_few_args(capsys):
    Set(REG("R1")).verify()
    captured = capsys.readouterr()
    assert "SET" in captured.err
    assert "too few" in captured.err


def test_SET_verify_with_too_many_args(capsys):
    Set(REG("R1"), 10, 11).verify()
    captured = capsys.readouterr()
    assert "SET" in captured.err
    assert "too many" in captured.err


# TODO: test_SETLO_verify_*


def test_SETLO_with_positive(vm):
    Setlo("R5", 23).execute(vm)
    assert vm.registers[5] == 23


def test_SETLO_with_negative(vm):
    Setlo("R9", -12).execute(vm)
    assert vm.registers[9] == to_u16(-12)


def test_SETLO_with_max_positive(vm):
    Setlo("R2", 127).execute(vm)
    assert vm.registers[2] == 127


def test_SETLO_with_255(vm):
    Setlo("R2", 255).execute(vm)
    assert vm.registers[2] == to_u16(-1)


def test_SETLO_with_max_negative(vm):
    Setlo("R2", -128).execute(vm)
    assert vm.registers[2] == to_u16(-128)


def test_SETLO_clears_high_bits(vm):
    vm.registers[6] = 4765
    Setlo("R6", 68).execute(vm)
    assert vm.registers[6] == 68


def test_SETLO_increments_pc(vm):
    Setlo("R9", -12).execute(vm)
    assert vm.pc == 1


def test_SETLO_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False
    Setlo("R7", 0).execute(vm)
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_SETLO_does_not_set_zero_flag(vm):
    Setlo("R7", 0).execute(vm)
    assert not vm.flag_zero


def test_SETLO_does_not_set_sign_flag(vm):
    Setlo("R7", -1).execute(vm)
    assert not vm.flag_sign


def test_SETLO_does_not_change_R0(vm):
    Setlo("R0", 20).execute(vm)
    assert vm.registers[0] == 0
