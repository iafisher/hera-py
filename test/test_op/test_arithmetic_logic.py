import pytest

from lark import Token

from hera.op import And, Or, Xor
from hera.utils import to_u16
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def R(s):
    return Token("REGISTER", s)


def test_AND_verify_with_correct_args():
    assert And(R("R1"), R("R2"), R("R3")).verify() == []


def test_AND_verify_with_too_few_args():
    errors = And(R("R1"), R("R2")).verify()
    assert len(errors) == 1
    assert "AND" in errors[0].msg
    assert "too few" in errors[0].msg


def test_AND_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    And("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 27


def test_AND_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    And("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 2


def test_AND_increments_pc(vm):
    And("R0", "R1", "R2").execute(vm)
    assert vm.pc == 1


def test_AND_big_numbers(vm):
    vm.registers[2] = 62434
    vm.registers[3] = 17589
    And("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 16544


def test_AND_sets_zero_flag(vm):
    vm.registers[2] = 82
    vm.registers[3] = 0
    And("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_AND_sets_sign_flag(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-37)
    And("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_AND_does_not_set_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    And("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_AND_does_not_clear_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.flag_carry = True
    vm.flag_overflow = True
    And("R1", "R2", "R3").execute(vm)
    assert vm.flag_carry
    assert vm.flag_overflow


def test_AND_does_not_affect_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 1
    And("R0", "R1", "R2").execute(vm)
    assert vm.registers[0] == 0


def test_OR_verify_with_too_many_args():
    errors = Or(R("R1"), R("R2"), R("R3"), R("R4")).verify()
    assert len(errors) == 1
    assert "OR" in errors[0].msg
    assert "too many" in errors[0].msg


def test_OR_verify_with_correct_args():
    assert Or(R("R1"), R("R2"), R("R3")).verify() == []


def test_OR_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    Or("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 27


def test_OR_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    Or("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 7


def test_OR_increments_pc(vm):
    Or("R0", "R1", "R2").execute(vm)
    assert vm.pc == 1


def test_OR_big_numbers(vm):
    vm.registers[2] = 8199
    vm.registers[3] = 762
    Or("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 8959


def test_OR_sets_zero_flag(vm):
    vm.registers[2] = 0
    vm.registers[3] = 0
    Or("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_OR_sets_sign_flag(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-37)
    Or("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_OR_does_not_set_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    Or("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == to_u16(-1)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_OR_does_not_clear_other_flags(vm):
    vm.registers[2] = to_u16(-1)
    vm.registers[3] = to_u16(-1)
    vm.flag_carry = True
    vm.flag_overflow = True
    Or("R1", "R2", "R3").execute(vm)
    assert vm.flag_carry
    assert vm.flag_overflow


def test_OR_does_not_affect_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 1
    Or("R0", "R1", "R2").execute(vm)
    assert vm.registers[0] == 0


def test_XOR_verify_with_too_few_args():
    errors = Xor(R("R1"), R("R2")).verify()
    assert len(errors) == 1
    assert "XOR" in errors[0].msg
    assert "too few" in errors[0].msg


def test_XOR_verify_with_correct_args():
    assert Xor(R("R1"), R("R2"), R("R3")).verify() == []


def test_XOR_same_numbers(vm):
    vm.registers[2] = 27
    vm.registers[3] = 27
    Xor("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 0


def test_XOR_different_numbers(vm):
    vm.registers[2] = 3  # 011
    vm.registers[3] = 6  # 110
    Xor("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 5


def test_XOR_increments_pc(vm):
    Xor("R0", "R1", "R2").execute(vm)
    assert vm.pc == 1


def test_XOR_big_numbers(vm):
    vm.registers[2] = 8199
    vm.registers[3] = 762
    Xor("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 8957


def test_XOR_sets_zero_flag(vm):
    vm.registers[2] = 0
    vm.registers[3] = 0
    Xor("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == 0
    assert vm.flag_zero
    assert not vm.flag_sign


def test_XOR_sets_sign_flag(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)
    Xor("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_zero
    assert vm.flag_sign


def test_XOR_does_not_set_other_flags(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)
    Xor("R1", "R2", "R3").execute(vm)
    assert vm.registers[1] == to_u16(-37)
    assert not vm.flag_carry
    assert not vm.flag_overflow


def test_XOR_does_not_clear_other_flags(vm):
    vm.registers[2] = 0
    vm.registers[3] = to_u16(-37)
    vm.flag_carry = True
    vm.flag_overflow = True
    Xor("R1", "R2", "R3").execute(vm)
    assert vm.flag_carry
    assert vm.flag_overflow


def test_XOR_does_not_affect_R0(vm):
    vm.registers[1] = 1
    vm.registers[2] = 0
    Xor("R0", "R1", "R2").execute(vm)
    assert vm.registers[0] == 0
