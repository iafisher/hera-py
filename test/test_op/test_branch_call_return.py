import pytest
from unittest.mock import patch

from hera.data import Op
from hera.vm import VirtualMachine


@pytest.fixture
def vm():
    return VirtualMachine()


def test_exec_one_delegates_to_br(vm):
    with patch("hera.vm.VirtualMachine.exec_br") as mock_exec_br:
        vm.exec_one(Op("BR", ["R1"]))
        assert mock_exec_br.call_count == 1
        assert mock_exec_br.call_args == (("R1",), {})


def test_br_sets_pc(vm):
    vm.registers[7] = 170
    vm.exec_br("R7")
    assert vm.pc == 170


def test_br_sets_pc_to_zero(vm):
    vm.exec_br("R0")
    assert vm.pc == 0


def test_br_does_not_change_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.registers[7] = 92
    vm.exec_br("R7")
    assert vm.pc == 92
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_brr(vm):
    with patch("hera.vm.VirtualMachine.exec_brr") as mock_exec_brr:
        vm.exec_one(Op("BRR", [12]))
        assert mock_exec_brr.call_count == 1
        assert mock_exec_brr.call_args == ((12,), {})


def test_brr_sets_pc(vm):
    vm.exec_brr(100)
    assert vm.pc == 100


def test_brr_with_negative_offset(vm):
    vm.pc = 50
    vm.exec_brr(-17)
    assert vm.pc == 33


def test_brr_sets_pc_with_previous_value(vm):
    vm.pc = 100
    vm.exec_brr(15)
    assert vm.pc == 115


def test_brr_sets_pc_to_zero(vm):
    vm.exec_brr(0)
    assert vm.pc == 0


def test_brr_does_not_change_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_brr(16)
    assert vm.pc == 16
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bl(vm):
    with patch("hera.vm.VirtualMachine.exec_bl") as mock_exec_bl:
        vm.exec_one(Op("BL", ["R3"]))
        assert mock_exec_bl.call_count == 1
        assert mock_exec_bl.call_args == (("R3",), {})


def test_bl_branches_on_sign(vm):
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_bl("R3")
    assert vm.pc == 47


def test_bl_branches_on_overflow(vm):
    vm.flag_overflow = True
    vm.registers[3] = 47
    vm.exec_bl("R3")
    assert vm.pc == 47


def test_bl_does_not_branch_on_sign_and_overflow(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.registers[3] = 47
    vm.exec_bl("R3")
    assert vm.pc == 1


def test_bl_does_not_branch_on_neither_sign_nor_overflow(vm):
    vm.registers[3] = 47
    vm.exec_bl("R3")
    assert vm.pc == 1


def test_bl_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bl("R0")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_blr(vm):
    with patch("hera.vm.VirtualMachine.exec_blr") as mock_exec_blr:
        vm.exec_one(Op("BLR", [20]))
        assert mock_exec_blr.call_count == 1
        assert mock_exec_blr.call_args == ((20,), {})


def test_blr_branches_on_sign(vm):
    vm.flag_sign = True
    vm.pc = 100
    vm.exec_blr(20)
    assert vm.pc == 120


def test_blr_branches_on_overflow(vm):
    vm.flag_overflow = True
    vm.pc = 100
    vm.exec_blr(-20)
    assert vm.pc == 80


def test_blr_does_not_branch_on_sign_and_overflow(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.pc = 100
    vm.exec_blr(20)
    assert vm.pc == 101


def test_blr_does_not_branch_on_neither_sign_nor_overflow(vm):
    vm.pc = 100
    vm.exec_blr(20)
    assert vm.pc == 101


def test_blr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_blr(20)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bge(vm):
    with patch("hera.vm.VirtualMachine.exec_bge") as mock_exec_bge:
        vm.exec_one(Op("BGE", ["R3"]))
        assert mock_exec_bge.call_count == 1
        assert mock_exec_bge.call_args == (("R3",), {})


def test_bge_branches_on_no_flags(vm):
    vm.registers[3] = 47
    vm.exec_bge("R3")
    assert vm.pc == 47


def test_bge_branches_on_sign_and_overflow(vm):
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_bge("R3")
    assert vm.pc == 47


def test_bge_does_not_branch_on_sign(vm):
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_bge("R3")
    assert vm.pc == 1


def test_bge_does_not_branch_on_overflow(vm):
    vm.flag_overflow = True
    vm.registers[3] = 47
    vm.exec_bge("R3")
    assert vm.pc == 1


def test_bge_branches_on_zero(vm):
    vm.flag_zero = True
    vm.registers[3] = 47
    vm.exec_bge("R3")
    assert vm.pc == 47


def test_bge_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bge("R0")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bger(vm):
    with patch("hera.vm.VirtualMachine.exec_bger") as mock_exec_bger:
        vm.exec_one(Op("BGER", [20]))
        assert mock_exec_bger.call_count == 1
        assert mock_exec_bger.call_args == ((20,), {})


def test_bger_branches_on_no_flags(vm):
    vm.exec_bger(47)
    assert vm.pc == 47


def test_bger_branches_on_sign_and_overflow(vm):
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.pc = 100
    vm.exec_bger(47)
    assert vm.pc == 147


def test_bger_does_not_branch_on_sign(vm):
    vm.flag_sign = True
    vm.exec_bger(47)
    assert vm.pc == 1


def test_bger_does_not_branch_on_overflow(vm):
    vm.flag_overflow = True
    vm.pc = 100
    vm.exec_bger(47)
    assert vm.pc == 101


def test_bger_branches_on_zero(vm):
    vm.flag_zero = True
    vm.exec_bger(47)
    assert vm.pc == 47


def test_bger_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bger(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_ble(vm):
    with patch("hera.vm.VirtualMachine.exec_ble") as mock_exec_ble:
        vm.exec_one(Op("BLE", ["R3"]))
        assert mock_exec_ble.call_count == 1
        assert mock_exec_ble.call_args == (("R3",), {})


def test_ble_branches_on_sign(vm):
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_ble("R3")
    assert vm.pc == 47


def test_ble_branches_on_overflow(vm):
    vm.flag_overflow = True
    vm.registers[3] = 47
    vm.exec_ble("R3")
    assert vm.pc == 47


def test_ble_branches_on_zero(vm):
    vm.flag_zero = True
    vm.registers[3] = 47
    vm.exec_ble("R3")
    assert vm.pc == 47


def test_ble_branches_on_overflow_and_zero(vm):
    vm.flag_overflow = True
    vm.flag_zero = True
    vm.registers[3] = 47
    vm.exec_ble("R3")
    assert vm.pc == 47


def test_ble_does_not_branch_on_no_flags(vm):
    vm.registers[3] = 47
    vm.exec_ble("R3")
    assert vm.pc == 1


def test_ble_does_not_branch_on_sign_and_overflow(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.registers[3] = 47
    vm.exec_ble("R3")
    assert vm.pc == 1


def test_ble_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_ble("R0")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bler(vm):
    with patch("hera.vm.VirtualMachine.exec_bler") as mock_exec_bler:
        vm.exec_one(Op("BLER", [47]))
        assert mock_exec_bler.call_count == 1
        assert mock_exec_bler.call_args == ((47,), {})


def test_bler_branches_on_sign(vm):
    vm.flag_sign = True
    vm.exec_bler(47)
    assert vm.pc == 47


def test_bler_branches_on_overflow(vm):
    vm.flag_overflow = True
    vm.pc = 100
    vm.exec_bler(47)
    assert vm.pc == 147


def test_bler_branches_on_zero(vm):
    vm.flag_zero = True
    vm.exec_bler(47)
    assert vm.pc == 47


def test_bler_branches_on_overflow_and_zero(vm):
    vm.flag_overflow = True
    vm.flag_zero = True
    vm.exec_bler(47)
    assert vm.pc == 47


def test_bler_does_not_branch_on_no_flags(vm):
    vm.exec_bler(47)
    assert vm.pc == 1


def test_bler_does_not_branch_on_sign_and_overflow(vm):
    vm.flag_sign = True
    vm.flag_overflow = True
    vm.pc = 100
    vm.exec_bler(47)
    assert vm.pc == 101


def test_bler_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bler(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bg(vm):
    with patch("hera.vm.VirtualMachine.exec_bg") as mock_exec_bg:
        vm.exec_one(Op("BG", ["R3"]))
        assert mock_exec_bg.call_count == 1
        assert mock_exec_bg.call_args == (("R3",), {})


def test_bg_branches_on_no_flags(vm):
    vm.registers[3] = 47
    vm.exec_bg("R3")
    assert vm.pc == 47


def test_bg_branches_on_sign_and_overflow(vm):
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_bg("R3")
    assert vm.pc == 47


def test_bg_does_not_branch_on_sign(vm):
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_bg("R3")
    assert vm.pc == 1


def test_bg_does_not_branch_on_overflow(vm):
    vm.flag_overflow = True
    vm.registers[3] = 47
    vm.exec_bg("R3")
    assert vm.pc == 1


def test_bg_does_not_branch_on_zero(vm):
    vm.flag_zero = True
    vm.registers[3] = 47
    vm.exec_bg("R3")
    assert vm.pc == 1


def test_bg_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bg("R0")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bgr(vm):
    with patch("hera.vm.VirtualMachine.exec_bgr") as mock_exec_bgr:
        vm.exec_one(Op("BGR", [20]))
        assert mock_exec_bgr.call_count == 1
        assert mock_exec_bgr.call_args == ((20,), {})


def test_bgr_branches_on_no_flags(vm):
    vm.exec_bgr(47)
    assert vm.pc == 47


def test_bgr_branches_on_sign_and_overflow(vm):
    vm.flag_overflow = True
    vm.flag_sign = True
    vm.pc = 100
    vm.exec_bgr(47)
    assert vm.pc == 147


def test_bgr_does_not_branch_on_sign(vm):
    vm.flag_sign = True
    vm.exec_bgr(47)
    assert vm.pc == 1


def test_bgr_does_not_branch_on_overflow(vm):
    vm.flag_overflow = True
    vm.pc = 100
    vm.exec_bgr(47)
    assert vm.pc == 101


def test_bgr_does_not_branch_on_zero(vm):
    vm.flag_zero = True
    vm.exec_bgr(47)
    assert vm.pc == 1


def test_bgr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bgr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bule(vm):
    with patch("hera.vm.VirtualMachine.exec_bule") as mock_exec_bule:
        vm.exec_one(Op("BULE", ["R3"]))
        assert mock_exec_bule.call_count == 1
        assert mock_exec_bule.call_args == (("R3",), {})


def test_bule_branches_on_not_carry(vm):
    vm.flag_carry = False
    vm.registers[3] = 47
    vm.exec_bule("R3")
    assert vm.pc == 47


def test_bule_does_not_branch_on_overflow(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.registers[3] = 47
    vm.exec_bule("R3")
    assert vm.pc == 1


def test_bule_branches_on_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = True
    vm.registers[3] = 47
    vm.exec_bule("R3")
    assert vm.pc == 47


def test_bule_does_not_branch_on_sign(vm):
    vm.flag_carry = True
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_bule("R3")
    assert vm.pc == 1


def test_bule_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bule("R0")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_buler(vm):
    with patch("hera.vm.VirtualMachine.exec_buler") as mock_exec_buler:
        vm.exec_one(Op("BULER", ["R3"]))
        assert mock_exec_buler.call_count == 1
        assert mock_exec_buler.call_args == (("R3",), {})


def test_buler_branches_on_not_carry(vm):
    vm.flag_carry = False
    vm.exec_buler(47)
    assert vm.pc == 47


def test_buler_does_not_branch_on_overflow(vm):
    vm.flag_carry = True
    vm.flag_overflow = True
    vm.pc = 100
    vm.exec_buler(47)
    assert vm.pc == 101


def test_buler_branches_on_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = True
    vm.pc = 100
    vm.exec_buler(47)
    assert vm.pc == 147


def test_buler_does_not_branch_on_sign(vm):
    vm.flag_carry = True
    vm.flag_sign = True
    vm.exec_buler(47)
    assert vm.pc == 1


def test_buler_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_buler(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bug(vm):
    with patch("hera.vm.VirtualMachine.exec_bug") as mock_exec_bug:
        vm.exec_one(Op("BUG", ["R3"]))
        assert mock_exec_bug.call_count == 1
        assert mock_exec_bug.call_args == (("R3",), {})


def test_bug_branches_on_carry_and_not_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = False
    vm.registers[3] = 47
    vm.exec_bug("R3")
    assert vm.pc == 47


def test_bug_does_not_branch_on_carry_and_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = True
    vm.registers[3] = 47
    vm.exec_bug("R3")
    assert vm.pc == 1


def test_bug_does_not_branch_on_not_carry_and_not_zero(vm):
    vm.registers[3] = 47
    vm.exec_bug("R3")
    assert vm.pc == 1


def test_bug_does_not_branch_on_sign(vm):
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_bug("R3")
    assert vm.pc == 1


def test_bug_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bug("R0")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bugr(vm):
    with patch("hera.vm.VirtualMachine.exec_bugr") as mock_exec_bugr:
        vm.exec_one(Op("BUGR", [47]))
        assert mock_exec_bugr.call_count == 1
        assert mock_exec_bugr.call_args == ((47,), {})


def test_bugr_branches_on_carry_and_not_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = False
    vm.exec_bugr(47)
    assert vm.pc == 47


def test_bugr_does_not_branch_on_carry_and_zero(vm):
    vm.flag_carry = True
    vm.flag_zero = True
    vm.pc = 100
    vm.exec_bugr(47)
    assert vm.pc == 101


def test_bugr_does_not_branch_on_not_carry_and_not_zero(vm):
    vm.exec_bugr(47)
    assert vm.pc == 1


def test_bugr_does_not_branch_on_sign(vm):
    vm.flag_sign = True
    vm.exec_bugr(47)
    assert vm.pc == 1


def test_bugr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bugr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bz(vm):
    with patch("hera.vm.VirtualMachine.exec_bz") as mock_exec_bz:
        vm.exec_one(Op("BZ", ["R3"]))
        assert mock_exec_bz.call_count == 1
        assert mock_exec_bz.call_args == (("R3",), {})


def test_bz_branches_on_zero(vm):
    vm.flag_zero = True
    vm.registers[3] = 47
    vm.exec_bz("R3")
    assert vm.pc == 47


def test_bz_does_not_branch_on_not_zero(vm):
    vm.registers[3] = 47
    vm.exec_bz("R3")
    assert vm.pc == 1


def test_bz_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bz("R3")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bzr(vm):
    with patch("hera.vm.VirtualMachine.exec_bzr") as mock_exec_bzr:
        vm.exec_one(Op("BZR", [47]))
        assert mock_exec_bzr.call_count == 1
        assert mock_exec_bzr.call_args == ((47,), {})


def test_bzr_branches_on_zero(vm):
    vm.flag_zero = True
    vm.pc = 100
    vm.exec_bzr(47)
    assert vm.pc == 147


def test_bzr_does_not_branch_on_not_zero(vm):
    vm.exec_bzr(47)
    assert vm.pc == 1


def test_bzr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bzr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bnz(vm):
    with patch("hera.vm.VirtualMachine.exec_bnz") as mock_exec_bnz:
        vm.exec_one(Op("BNZ", ["R3"]))
        assert mock_exec_bnz.call_count == 1
        assert mock_exec_bnz.call_args == (("R3",), {})


def test_bnz_branches_on_not_zero(vm):
    vm.registers[3] = 47
    vm.exec_bnz("R3")
    assert vm.pc == 47


def test_bnz_does_not_branch_on_zero(vm):
    vm.flag_zero = True
    vm.registers[3] = 47
    vm.exec_bnz("R3")
    assert vm.pc == 1


def test_bnz_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bnz("R3")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bnzr(vm):
    with patch("hera.vm.VirtualMachine.exec_bnzr") as mock_exec_bnzr:
        vm.exec_one(Op("BNZR", [47]))
        assert mock_exec_bnzr.call_count == 1
        assert mock_exec_bnzr.call_args == ((47,), {})


def test_bnzr_branches_on_not_zero(vm):
    vm.pc = 100
    vm.exec_bnzr(47)
    assert vm.pc == 147


def test_bnzr_does_not_branch_on_zero(vm):
    vm.flag_zero = True
    vm.exec_bnzr(47)
    assert vm.pc == 1


def test_bnzr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bnzr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bc(vm):
    with patch("hera.vm.VirtualMachine.exec_bc") as mock_exec_bc:
        vm.exec_one(Op("BC", ["R3"]))
        assert mock_exec_bc.call_count == 1
        assert mock_exec_bc.call_args == (("R3",), {})


def test_bc_branches_on_carry(vm):
    vm.flag_carry = True
    vm.registers[3] = 47
    vm.exec_bc("R3")
    assert vm.pc == 47


def test_bc_does_not_branch_on_not_carry(vm):
    vm.registers[3] = 47
    vm.exec_bc("R3")
    assert vm.pc == 1


def test_bc_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bc("R3")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bcr(vm):
    with patch("hera.vm.VirtualMachine.exec_bcr") as mock_exec_bcr:
        vm.exec_one(Op("BCR", [47]))
        assert mock_exec_bcr.call_count == 1
        assert mock_exec_bcr.call_args == ((47,), {})


def test_bcr_branches_on_carry(vm):
    vm.flag_carry = True
    vm.pc = 100
    vm.exec_bcr(47)
    assert vm.pc == 147


def test_bcr_does_not_branch_on_not_carry(vm):
    vm.exec_bcr(47)
    assert vm.pc == 1


def test_bcr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bcr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bnc(vm):
    with patch("hera.vm.VirtualMachine.exec_bnc") as mock_exec_bnc:
        vm.exec_one(Op("BNC", ["R3"]))
        assert mock_exec_bnc.call_count == 1
        assert mock_exec_bnc.call_args == (("R3",), {})


def test_bnc_branches_on_not_carry(vm):
    vm.registers[3] = 47
    vm.exec_bnc("R3")
    assert vm.pc == 47


def test_bnc_does_not_branch_on_carry(vm):
    vm.flag_carry = True
    vm.registers[3] = 47
    vm.exec_bnc("R3")
    assert vm.pc == 1


def test_bnc_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bnc("R3")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bncr(vm):
    with patch("hera.vm.VirtualMachine.exec_bncr") as mock_exec_bncr:
        vm.exec_one(Op("BNCR", [47]))
        assert mock_exec_bncr.call_count == 1
        assert mock_exec_bncr.call_args == ((47,), {})


def test_bncr_branches_on_not_carry(vm):
    vm.pc = 100
    vm.exec_bncr(47)
    assert vm.pc == 147


def test_bncr_does_not_branch_on_carry(vm):
    vm.flag_carry = True
    vm.exec_bncr(47)
    assert vm.pc == 1


def test_bncr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bncr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bs(vm):
    with patch("hera.vm.VirtualMachine.exec_bs") as mock_exec_bs:
        vm.exec_one(Op("BS", ["R3"]))
        assert mock_exec_bs.call_count == 1
        assert mock_exec_bs.call_args == (("R3",), {})


def test_bs_branches_on_sign(vm):
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_bs("R3")
    assert vm.pc == 47


def test_bs_does_not_branch_on_not_sign(vm):
    vm.registers[3] = 47
    vm.exec_bs("R3")
    assert vm.pc == 1


def test_bs_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bs("R3")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bsr(vm):
    with patch("hera.vm.VirtualMachine.exec_bsr") as mock_exec_bsr:
        vm.exec_one(Op("BSR", [47]))
        assert mock_exec_bsr.call_count == 1
        assert mock_exec_bsr.call_args == ((47,), {})


def test_bsr_branches_on_sign(vm):
    vm.flag_sign = True
    vm.pc = 100
    vm.exec_bsr(47)
    assert vm.pc == 147


def test_bsr_does_not_branch_on_not_sign(vm):
    vm.exec_bsr(47)
    assert vm.pc == 1


def test_bsr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bsr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bns(vm):
    with patch("hera.vm.VirtualMachine.exec_bns") as mock_exec_bns:
        vm.exec_one(Op("BNS", ["R3"]))
        assert mock_exec_bns.call_count == 1
        assert mock_exec_bns.call_args == (("R3",), {})


def test_bns_branches_on_not_sign(vm):
    vm.registers[3] = 47
    vm.exec_bns("R3")
    assert vm.pc == 47


def test_bns_does_not_branch_on_sign(vm):
    vm.flag_sign = True
    vm.registers[3] = 47
    vm.exec_bns("R3")
    assert vm.pc == 1


def test_bns_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bns("R3")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bnsr(vm):
    with patch("hera.vm.VirtualMachine.exec_bnsr") as mock_exec_bnsr:
        vm.exec_one(Op("BNSR", [47]))
        assert mock_exec_bnsr.call_count == 1
        assert mock_exec_bnsr.call_args == ((47,), {})


def test_bnsr_branches_on_not_sign(vm):
    vm.pc = 100
    vm.exec_bnsr(47)
    assert vm.pc == 147


def test_bnsr_does_not_branch_on_sign(vm):
    vm.flag_sign = True
    vm.exec_bnsr(47)
    assert vm.pc == 1


def test_bnsr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bnsr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bv(vm):
    with patch("hera.vm.VirtualMachine.exec_bv") as mock_exec_bv:
        vm.exec_one(Op("BV", ["R3"]))
        assert mock_exec_bv.call_count == 1
        assert mock_exec_bv.call_args == (("R3",), {})


def test_bv_branches_on_overflow(vm):
    vm.flag_overflow = True
    vm.registers[3] = 47
    vm.exec_bv("R3")
    assert vm.pc == 47


def test_bv_does_not_branch_on_not_overflow(vm):
    vm.registers[3] = 47
    vm.exec_bv("R3")
    assert vm.pc == 1


def test_bv_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bv("R3")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bvr(vm):
    with patch("hera.vm.VirtualMachine.exec_bvr") as mock_exec_bvr:
        vm.exec_one(Op("BVR", [47]))
        assert mock_exec_bvr.call_count == 1
        assert mock_exec_bvr.call_args == ((47,), {})


def test_bvr_branches_on_overflow(vm):
    vm.flag_overflow = True
    vm.pc = 100
    vm.exec_bvr(47)
    assert vm.pc == 147


def test_bvr_does_not_branch_on_not_overflow(vm):
    vm.exec_bvr(47)
    assert vm.pc == 1


def test_bvr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bvr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bnv(vm):
    with patch("hera.vm.VirtualMachine.exec_bnv") as mock_exec_bnv:
        vm.exec_one(Op("BNV", ["R3"]))
        assert mock_exec_bnv.call_count == 1
        assert mock_exec_bnv.call_args == (("R3",), {})


def test_bnv_branches_on_not_overflow(vm):
    vm.registers[3] = 47
    vm.exec_bnv("R3")
    assert vm.pc == 47


def test_bnv_does_not_branch_on_overflow(vm):
    vm.flag_overflow = True
    vm.registers[3] = 47
    vm.exec_bnv("R3")
    assert vm.pc == 1


def test_bnv_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bnv("R3")
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_bnvr(vm):
    with patch("hera.vm.VirtualMachine.exec_bnvr") as mock_exec_bnvr:
        vm.exec_one(Op("BNVR", [47]))
        assert mock_exec_bnvr.call_count == 1
        assert mock_exec_bnvr.call_args == ((47,), {})


def test_bnvr_branches_on_not_overflow(vm):
    vm.pc = 100
    vm.exec_bnvr(47)
    assert vm.pc == 147


def test_bnvr_does_not_branch_on_overflow(vm):
    vm.flag_overflow = True
    vm.exec_bnvr(47)
    assert vm.pc == 1


def test_bnvr_does_not_set_flags(vm):
    vm.flag_sign = True
    vm.flag_zero = True
    vm.flag_overflow = True
    vm.flag_carry = True
    vm.flag_carry_block = True
    vm.exec_bnvr(47)
    assert vm.flag_sign
    assert vm.flag_zero
    assert vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_exec_one_delegates_to_call(vm):
    with patch("hera.vm.VirtualMachine.exec_call") as mock_exec_call:
        vm.exec_one(Op("CALL", ["R12", "R13"]))
        assert mock_exec_call.call_count == 1
        assert mock_exec_call.call_args == (("R12", "R13"), {})


def test_call_changes_pc(vm):
    vm.pc = 100
    vm.registers[13] = 40
    vm.exec_call("R12", "R13")
    assert vm.pc == 40


def test_call_updates_second_register(vm):
    vm.pc = 100
    vm.registers[13] = 40
    vm.exec_call("R12", "R13")
    assert vm.registers[13] == 101


def test_call_updates_frame_pointer(vm):
    vm.registers[12] = 600
    vm.registers[13] = 40
    vm.exec_call("R12", "R13")
    assert vm.registers[14] == 600


def test_call_updates_first_register(vm):
    vm.registers[14] = 550
    vm.registers[12] = 600
    vm.registers[13] = 40
    vm.exec_call("R12", "R13")
    assert vm.registers[12] == 550


def test_exec_one_delegates_to_return(vm):
    with patch("hera.vm.VirtualMachine.exec_return") as mock_exec_return:
        vm.exec_one(Op("RETURN", ["R12", "R13"]))
        assert mock_exec_return.call_count == 1
        assert mock_exec_return.call_args == (("R12", "R13"), {})


def test_return_changes_pc(vm):
    vm.pc = 100
    vm.registers[13] = 40
    vm.exec_return("R12", "R13")
    assert vm.pc == 40


def test_return_updates_second_register(vm):
    vm.pc = 100
    vm.registers[13] = 40
    vm.exec_return("R12", "R13")
    assert vm.registers[13] == 101


def test_return_updates_frame_pointer(vm):
    vm.registers[12] = 600
    vm.registers[13] = 40
    vm.exec_return("R12", "R13")
    assert vm.registers[14] == 600


def test_return_updates_first_register(vm):
    vm.registers[14] = 550
    vm.registers[12] = 600
    vm.registers[13] = 40
    vm.exec_return("R12", "R13")
    assert vm.registers[12] == 550
