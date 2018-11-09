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
    assert vm.flag_zero == False
    assert vm.flag_sign == False
    assert vm.flag_overflow == False
    assert vm.flag_carry == False
    assert vm.flag_carry_block == False
    for x in vm.memory:
        assert x == 0
