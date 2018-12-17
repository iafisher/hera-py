import pytest
from unittest.mock import patch

from hera.main import main, execute_program
from hera.symtab import HERA_DATA_START
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


def test_cs240_aslu_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/cs240/aslu.hera"], vm)

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


def test_cs240_branches_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/cs240/branches.hera"], vm)

    assert vm.registers[1] == 1
    assert vm.registers[2] == 2
    assert vm.registers[3] == 3
    assert vm.registers[4] == 4
    assert vm.registers[5] == 5
    assert vm.registers[6] == 6

    for r in vm.registers[7:11]:
        assert r == 0

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block


def test_cs240_fib_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/cs240/fib.hera"], vm)

    assert vm.registers[1] == 0
    assert vm.registers[2] == 0
    assert vm.registers[3] == 0
    assert vm.registers[4] == 0x000A
    assert vm.registers[5] == 0x0037
    assert vm.registers[6] == 0x0022
    assert vm.registers[7] == 0x0022
    assert vm.registers[8] == 0x000B
    assert vm.registers[9] == 0
    assert vm.registers[10] == 0

    assert vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_cs240_flag_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/cs240/flag.hera"], vm)

    assert vm.registers[1] == 0x0015
    assert vm.registers[2] == 0x0000
    assert vm.registers[3] == 0x001B
    assert vm.registers[4] == 0x0009
    assert vm.registers[5] == 0x0019
    assert vm.registers[6] == 0x0003
    assert vm.registers[7] == 0x0003
    assert vm.registers[8] == 0x0015
    assert vm.registers[9] == 0x0000
    assert vm.registers[10] == 0x0007

    assert vm.flag_sign
    assert not vm.flag_zero
    assert vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_cs240_stein_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/cs240/stein.hera"], vm)

    assert vm.registers[1] == 1
    assert vm.registers[2] == 1
    assert vm.registers[3] == 2
    assert vm.registers[4] == 1

    for r in vm.registers[5:11]:
        assert r == 0

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_cs240_factorial_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/cs240/factorial.hera"], vm)

    assert vm.registers[1] == 7
    assert vm.registers[2] == 5040

    for r in vm.registers[3:11]:
        assert r == 0

    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block


def test_cs240_extended_stein_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/cs240/extended_stein.hera"], vm)

    assert vm.registers[1] == 0x001
    assert vm.registers[2] == 0x001
    assert vm.registers[3] == 0x001
    assert vm.registers[4] == 0x0011
    assert vm.registers[5] == 0x0027
    assert vm.registers[6] == 0x0017
    assert vm.registers[7] == 0xFFF6
    assert vm.registers[8] == 0xFFF0
    assert vm.registers[9] == 0x0007
    assert vm.registers[10] == 0x0001

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_cs240_callret_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/cs240/callret.hera"], vm)

    assert vm.registers[1] == 0x0009
    assert vm.registers[2] == 0x0013

    for r in vm.registers[3:11]:
        assert r == 0

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block


def test_hera_boilerplate_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/hera_boilerplate.hera"], vm)

    assert vm.registers[1] == 42
    assert vm.registers[2] == 42

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_dskip_overflow_dot_hera(capsys):
    vm = VirtualMachine()
    with pytest.raises(SystemExit):
        main(["test/assets/dskip_overflow.hera"], vm)

    captured = capsys.readouterr()
    assert "DSKIP(0xFFFF)" in captured.err
    assert "line 1" in captured.err


def test_manual_strings_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/manual/strings.hera"], vm)

    assert vm.registers[1] == 3
    assert vm.registers[2] == 0xC033
    assert vm.registers[3] == 0
    assert vm.registers[4] == 63
    assert vm.registers[5] == 63

    for r in vm.registers[6:10]:
        assert r == 0

    s = "Is this an example? With three questions? Really?"
    assert vm.memory[HERA_DATA_START] == len(s)
    for i in range(len(s)):
        assert vm.memory[HERA_DATA_START + i + 1] == ord(s[i])

    assert vm.flag_carry_block
    assert not vm.flag_carry
    assert not vm.flag_overflow
    assert vm.flag_zero
    assert not vm.flag_sign


def test_simple_include_dot_hera():
    vm = VirtualMachine()
    main(["test/assets/simple_include.hera"], vm)

    assert vm.registers[1] == 20
    assert vm.registers[2] == 22
    assert vm.registers[3] == 42

    for r in vm.registers[4:11]:
        assert r == 0

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_error_message_for_missing_comma(capsys):
    line = "SETLO(R1 40)"
    with pytest.raises(SystemExit):
        execute_program(line)

    captured = capsys.readouterr()
    assert line in captured.err
    assert "line 1" in captured.err
    assert "col 10" in captured.err


def test_error_message_for_invalid_register(capsys):
    line = "SET(R17, 65)"
    with pytest.raises(SystemExit):
        execute_program(line)

    captured = capsys.readouterr()
    assert line in captured.err
    assert "line 1" in captured.err
    assert "col 5" in captured.err
    # Make sure the caret is aligned properly.
    assert "      ^" in captured.err
    assert "R17" in captured.err
    assert "not a valid register" in captured.err


def test_error_message_for_invalid_register_with_weird_syntax(capsys):
    line = "SET(\n\tR17,\n\t65)"
    with pytest.raises(SystemExit):
        execute_program(line)

    captured = capsys.readouterr()
    assert "\tR17" in captured.err
    assert "SET(" not in captured.err
    assert "65" not in captured.err
    assert "line 2" in captured.err
    assert "col 2" in captured.err
    # Make sure the caret is aligned properly.
    assert "  \t^" in captured.err
    assert "not a valid register" in captured.err


def test_multiple_error_messages(capsys):
    line = "ADD(R1, 10)\nINC(R4)"
    with pytest.raises(SystemExit):
        execute_program(line)

    captured = capsys.readouterr()
    assert "ADD" in captured.err
    assert "too few" in captured.err
    assert "not a register" in captured.err
    assert "line 1" in captured.err
    assert "INC" in captured.err
    assert "line 2" in captured.err
