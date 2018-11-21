import pytest
from unittest.mock import patch

from hera.main import main, execute_program
from hera.preprocessor import HERA_DATA_START
from hera.vm import VirtualMachine


def test_addition_dot_hera():
    vm = VirtualMachine()
    main(["test/hera/addition.hera"], vm)

    assert vm.registers[1] == 20
    assert vm.registers[2] == 22
    assert vm.registers[3] == 42
    for r in vm.registers[4:]:
        assert r == 0
    assert vm.flag_sign == False
    assert vm.flag_zero == False
    assert vm.flag_overflow == False
    assert vm.flag_carry == False
    assert vm.flag_carry_block == False
    for x in vm.memory:
        assert x == 0


def test_simple_loop_dot_hera():
    vm = VirtualMachine()
    main(["test/hera/simple_loop.hera"], vm)

    assert vm.registers[1] == 10
    assert vm.registers[2] == 10
    for r in vm.registers[3:10]:
        assert r == 0
    assert vm.flag_sign == False
    assert vm.flag_zero == True
    assert vm.flag_overflow == False
    assert vm.flag_carry == True
    assert vm.flag_carry_block == False
    for x in vm.memory:
        assert x == 0


def test_fcall_dot_hera():
    vm = VirtualMachine()
    main(["test/hera/fcall.hera"], vm)

    assert vm.registers[1] == 16
    for r in vm.registers[2:10]:
        assert r == 0
    assert vm.flag_sign == False
    assert vm.flag_zero == False
    assert vm.flag_overflow == False
    assert vm.flag_carry == False
    assert vm.flag_carry_block == False
    for x in vm.memory:
        assert x == 0


def test_fib_dot_hera():
    vm = VirtualMachine()
    main(["test/hera/fib.hera"], vm)

    assert vm.registers[1] == 12
    assert vm.registers[2] == 144
    assert vm.registers[3] == 89
    assert vm.registers[4] == 12
    assert vm.registers[5] == 89
    for r in vm.registers[6:10]:
        assert r == 0
    assert vm.flag_sign == False
    assert vm.flag_zero == True
    assert vm.flag_overflow == False
    assert vm.flag_carry == True
    assert vm.flag_carry_block == True
    for x in vm.memory:
        assert x == 0


def test_data_easy_dot_hera():
    vm = VirtualMachine()
    main(["test/hera/data_easy.hera"], vm)

    assert vm.registers[1] == HERA_DATA_START
    assert vm.registers[2] == 42
    for r in vm.registers[3:]:
        assert r == 0
    assert vm.flag_sign == False
    assert vm.flag_zero == False
    assert vm.flag_overflow == False
    assert vm.flag_carry == False
    assert vm.flag_carry_block == False
    assert vm.memory[HERA_DATA_START] == 42


def test_dskip_dot_hera():
    vm = VirtualMachine()
    main(["test/hera/dskip.hera"], vm)

    assert vm.registers[1] == HERA_DATA_START
    assert vm.registers[2] == 42
    assert vm.registers[3] == 84
    for r in vm.registers[4:]:
        assert r == 0
    assert vm.flag_sign == False
    assert vm.flag_zero == False
    assert vm.flag_overflow == False
    assert vm.flag_carry == False
    assert vm.flag_carry_block == False
    assert vm.memory[HERA_DATA_START] == 42
    assert vm.memory[HERA_DATA_START + 11] == 84


def test_loop_and_constant_dot_hera():
    vm = VirtualMachine()
    main(["test/hera/loop_and_constant.hera"], vm)

    assert vm.registers[1] == 100
    assert vm.registers[2] == 100
    assert vm.registers[3] == 5050
    for r in vm.registers[4:10]:
        assert r == 0
    assert vm.flag_sign == False
    assert vm.flag_zero == True
    assert vm.flag_overflow == False
    assert vm.flag_carry == True
    assert vm.flag_carry_block == False


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
        assert "R17" in msg
        assert "not a valid register" in msg
