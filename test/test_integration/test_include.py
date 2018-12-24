from hera.main import main
from hera.vm import VirtualMachine


def test_simple_include_program():
    vm = VirtualMachine()
    main(["test/assets/include/simple.hera"], vm)

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
