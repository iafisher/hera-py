from hera.data import DEFAULT_DATA_START
from hera.main import main
from hera.vm import VirtualMachine


def test_aslu_program(capsys):
    vm = main(["test/assets/cs240/aslu.hera"])

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

    assert "Warning" not in capsys.readouterr().err


def test_branches_program():
    vm = main(["test/assets/cs240/branches.hera"])

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

    # This code does give a warning on account of C++ boilerplate.


def test_fibonacci_program():
    vm = main(["test/assets/cs240/fib.hera"])

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

    # This code does give a warning on account of C++ boilerplate.


def test_flag_program():
    vm = main(["test/assets/cs240/flag.hera"])

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

    # This code does give a warning on account of C++ boilerplate.


def test_stein_program():
    vm = main(["test/assets/cs240/stein.hera"])

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

    # This code does give a warning on account of C++ boilerplate.


def test_factorial_program(capsys):
    vm = main(["test/assets/cs240/factorial.hera"])

    assert vm.registers[1] == 7
    assert vm.registers[2] == 5040

    for r in vm.registers[3:11]:
        assert r == 0

    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert vm.flag_carry_block

    assert "Warning" not in capsys.readouterr().err


def test_extended_stein_program():
    vm = main(["test/assets/cs240/extended_stein.hera"])

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

    # This code does give a warning on account of C++ boilerplate.


def test_call_and_return_program(capsys):
    vm = main(["test/assets/cs240/call_and_return.hera"])

    assert vm.registers[1] == 0x0009
    assert vm.registers[2] == 0x0013

    for r in vm.registers[3:11]:
        assert r == 0

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert vm.flag_carry_block

    assert "Warning" not in capsys.readouterr().err


def test_array_program():
    vm = main(["test/assets/cs240/array.hera"])

    assert vm.registers[5] == 5050

    for r in vm.registers[6:11]:
        assert r == 0

    assert not vm.flag_sign
    assert vm.flag_zero
    assert not vm.flag_overflow
    assert vm.flag_carry
    assert not vm.flag_carry_block

    for i in range(100):
        assert vm.memory[DEFAULT_DATA_START + i] == i + 1
    assert vm.memory[DEFAULT_DATA_START + 100] == 5050
