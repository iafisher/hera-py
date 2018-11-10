import pytest

from hera.assembler import HERA_DATA_START
from hera.main import execute_program
from hera.vm import VirtualMachine


def test_addition_dot_hera():
    with open('test/hera/addition.hera') as f:
        vm = execute_program(f.read())

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
    with open('test/hera/simple_loop.hera') as f:
        vm = execute_program(f.read())


def test_fcall_dot_hera():
    with open('test/hera/fcall.hera') as f:
        vm = execute_program(f.read())

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
    with open('test/hera/fib.hera') as f:
        vm = execute_program(f.read())

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
    with open('test/hera/data_easy.hera') as f:
        vm = execute_program(f.read())

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
    with open('test/hera/dskip.hera') as f:
        vm = execute_program(f.read())

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
    assert vm.memory[HERA_DATA_START+11] == 84


def test_loop_and_constant_dot_hera():
    with open('test/hera/loop_and_constant.hera') as f:
        vm = execute_program(f.read())

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
