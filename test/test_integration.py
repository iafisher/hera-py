import pytest
from unittest.mock import patch

from hera.main import main, execute_program
from hera.preprocessor import HERA_DATA_START
from hera.vm import VirtualMachine


def test_addition_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/addition.hera"], vm)

    assert vm.registers[1] == 20
    assert vm.registers[2] == 22
    assert vm.registers[3] == 42
    for r in vm.registers[4:]:
        assert r == 0
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block
    for x in vm.memory:
        assert x == 0


def test_simple_loop_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/simple_loop.hera"], vm)

    assert vm.registers[1] == 10
    assert vm.registers[2] == 10
    for r in vm.registers[3:10]:
        assert r == 0
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block
    for x in vm.memory:
        assert x == 0


def test_fcall_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/fcall.hera"], vm)

    assert vm.registers[1] == 16
    for r in vm.registers[2:10]:
        assert r == 0
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block
    for x in vm.memory:
        assert x == 0


def test_fib_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/fib.hera"], vm)

    assert vm.registers[1] == 12
    assert vm.registers[2] == 144
    assert vm.registers[3] == 89
    assert vm.registers[4] == 12
    assert vm.registers[5] == 89
    for r in vm.registers[6:10]:
        assert r == 0
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block
    for x in vm.memory:
        assert x == 0


def test_data_easy_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/data_easy.hera"], vm)

    assert vm.registers[1] == HERA_DATA_START
    assert vm.registers[2] == 42
    for r in vm.registers[3:]:
        assert r == 0
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block
    assert vm.memory[HERA_DATA_START] == 42


def test_dskip_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/dskip.hera"], vm)

    assert vm.registers[1] == HERA_DATA_START
    assert vm.registers[2] == 42
    assert vm.registers[3] == 84
    for r in vm.registers[4:]:
        assert r == 0
    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block
    assert vm.memory[HERA_DATA_START] == 42
    assert vm.memory[HERA_DATA_START + 11] == 84


def test_loop_and_constant_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/loop_and_constant.hera"], vm)

    assert vm.registers[1] == 100
    assert vm.registers[2] == 100
    assert vm.registers[3] == 5050
    for r in vm.registers[4:10]:
        assert r == 0
    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_cs240_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/cs240.hera"], vm)

    assert vm.registers[1] == 0xBFF2
    assert vm.registers[2] == 0xF000
    assert vm.registers[3] == 0x0010
    assert vm.registers[4] == 0x7000
    assert vm.registers[5] == 0x8010
    assert vm.registers[6] == 0x7800
    assert vm.registers[7] == 0x0070
    assert vm.registers[8] == 0xE009
    assert vm.registers[9] == 0xFFC8
    assert vm.registers[10] == 0x3C00

    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_error_message_for_missing_comma():
    line = "SETLO(R1 40)"
    with patch("hera.main.error_and_exit") as mock_exit:
        execute_program(line)
        msg = mock_exit.call_args[0][0]
        assert line in msg
        assert "line 1" in msg
        assert "col 10" in msg


def test_error_message_for_invalid_register():
    line = "SET(R17, 65)"
    with patch("hera.main.error_and_exit") as mock_exit:
        execute_program(line)
        msg = mock_exit.call_args[0][0]
        assert line in msg
        assert "line 1" in msg
        assert "col 5" in msg
        # Make sure the caret is aligned properly.
        assert "      ^" in msg
        assert "R17" in msg
        assert "not a valid register" in msg


def test_error_message_for_invalid_register_with_weird_syntax():
    line = "SET(\n\tR17,\n\t65)"
    with patch("hera.main.error_and_exit") as mock_exit:
        execute_program(line)
        msg = mock_exit.call_args[0][0]
        assert "\tR17" in msg
        assert "SET(" not in msg
        assert "65" not in msg
        assert "line 2" in msg
        assert "col 2" in msg
        # Make sure the caret is aligned properly.
        assert "  \t^" in msg
        assert "not a valid register" in msg
