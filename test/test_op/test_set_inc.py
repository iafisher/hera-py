import pytest

from lark import Token

from hera.op import Inc, Set, Sethi, Setlo
from hera.utils import HERAError, IntToken, to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def R(s):
    return Token("REGISTER", s)


def I(n):
    return IntToken(n)


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


def test_SET_verify_with_too_few_args():
    errors = Set(R("R1")).verify()
    assert len(errors) == 1
    assert "SET" in errors[0].msg
    assert "too few" in errors[0].msg


def test_SET_verify_with_too_many_args():
    errors = Set(R("R1"), 10, 11).verify()
    assert len(errors) == 1
    assert "SET" in errors[0].msg
    assert "too many" in errors[0].msg


def test_SET_verify_with_integer_out_of_range():
    errors = Set(R("R1"), I(-32769)).verify()
    assert len(errors) == 1
    assert "SET" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_SET_verify_with_another_integer_out_of_range():
    errors = Set(R("R1"), I(65536)).verify()
    assert len(errors) == 1
    assert "SET" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_SET_verify_with_correct_args():
    assert Set(R("R1"), -32768).verify() == []
    assert Set(R("R1"), 65535).verify() == []
    assert Set(R("R1"), 0).verify() == []


def test_SETLO_verify_with_too_many_args():
    errors = Setlo(R("R5"), 1, 2).verify()
    assert len(errors) == 1
    assert "SETLO" in errors[0].msg
    assert "too many" in errors[0].msg


def test_SETLO_verify_with_too_few_args():
    errors = Setlo(R("R5")).verify()
    assert len(errors) == 1
    assert "SETLO" in errors[0].msg
    assert "too few" in errors[0].msg


def test_SETLO_verify_with_integer_out_of_range():
    errors = Setlo(R("R5"), I(-129)).verify()
    assert len(errors) == 1
    assert "SETLO" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_SETLO_verify_with_another_integer_out_of_range():
    errors = Setlo(R("R5"), I(256)).verify()
    assert len(errors) == 1
    assert "SETLO" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_SETLO_verify_with_correct_args():
    assert Setlo(R("R5"), -128).verify() == []
    assert Setlo(R("R5"), 255).verify() == []
    assert Setlo(R("R5"), 0).verify() == []


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


def test_SETHI_verify_with_integer_out_of_range():
    errors = Sethi(R("R5"), I(-129)).verify()
    assert len(errors) == 1
    assert "SETHI" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_SETHI_verify_with_another_integer_out_of_range():
    errors = Sethi(R("R5"), I(256)).verify()
    assert len(errors) == 1
    assert "SETHI" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_SETHI_verify_with_correct_args():
    assert Sethi(R("R5"), -128).verify() == []
    assert Sethi(R("R5"), 255).verify() == []
    assert Sethi(R("R5"), 0).verify() == []


def test_SETHI_with_positive(vm):
    Sethi("R5", 23).execute(vm)
    assert vm.registers[5] == 5888


def test_SETHI_with_max_positive(vm):
    Sethi("R2", 255).execute(vm)
    assert vm.registers[2] == 65280


def test_SETHI_does_not_clear_low_bits(vm):
    vm.registers[6] = 4765
    Sethi("R6", 68).execute(vm)
    assert vm.registers[6] == 17565


def test_SETHI_increments_pc(vm):
    Sethi("R9", 12).execute(vm)
    assert vm.pc == 1


def test_SETHI_ignores_flags(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.flag_zero = False
    Sethi("R7", 0).execute(vm)
    assert vm.flag_carry
    assert vm.flag_overflow
    assert vm.flag_sign
    assert not vm.flag_zero


def test_SETHI_does_not_set_zero_flag(vm):
    Sethi("R7", 0).execute(vm)
    assert not vm.flag_zero


def test_SETHI_does_not_set_sign_flag(vm):
    Sethi("R7", -1).execute(vm)
    assert not vm.flag_sign


def test_SETHI_does_not_change_R0(vm):
    Sethi("R0", 20).execute(vm)
    assert vm.registers[0] == 0


def test_INC_verify_with_integer_out_of_range():
    errors = Inc(R("R1"), I(65)).verify()
    assert len(errors) == 1
    assert "INC" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_INC_verify_with_zero():
    errors = Inc(R("R1"), I(0)).verify()
    assert len(errors) == 1
    assert "INC" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_INC_verify_with_negative_integer():
    errors = Inc(R("R1"), I(-1)).verify()
    assert len(errors) == 1
    assert "INC" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_INC_verify_with_negative_integer():
    errors = Inc(R("R1"), I(-1)).verify()
    assert len(errors) == 1
    assert "INC" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_INC_verify_with_correct_args():
    assert Inc(R("R1"), 64).verify() == []
    assert Inc(R("R1"), 1).verify() == []
    assert Inc(R("R1"), 24).verify() == []


def test_INC_with_small_positive(vm):
    Inc("R8", 6).execute(vm)
    assert vm.registers[8] == 6


def test_INC_with_max(vm):
    Inc("R2", 32).execute(vm)
    assert vm.registers[2] == 32


def test_INC_with_previous_value(vm):
    vm.registers[5] = 4000
    Inc("R5", 2).execute(vm)
    assert vm.registers[5] == 4002


def test_INC_with_previous_negative_value(vm):
    vm.registers[9] = to_u16(-12)
    Inc("R9", 10).execute(vm)
    assert vm.registers[9] == to_u16(-2)


def test_INC_increments_pc(vm):
    Inc("R1", 1).execute(vm)
    assert vm.pc == 1


def test_INC_sets_zero_flag(vm):
    vm.registers[7] = to_u16(-1)
    Inc("R7", 1).execute(vm)
    assert vm.registers[7] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_INC_sets_sign_flag(vm):
    vm.registers[1] = 32765
    Inc("R1", 5).execute(vm)
    assert vm.registers[1] == to_u16(-32766)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_INC_sets_carry_flag(vm):
    vm.registers[8] = to_u16(-1)
    Inc("R8", 1).execute(vm)
    assert vm.flag_carry
    assert not vm.flag_overflow


def test_INC_sets_overflow_flag(vm):
    vm.registers[8] = 32765
    Inc("R8", 5).execute(vm)
    assert not vm.flag_carry
    assert vm.flag_overflow


def test_INC_ignores_incoming_carry(vm):
    vm.flag_carry = True
    Inc("R8", 5).execute(vm)
    assert vm.registers[8] == 5
    assert not vm.flag_carry


def test_INC_does_not_affect_R0(vm):
    Inc("R0", 1).execute(vm)
    assert vm.registers[0] == 0
