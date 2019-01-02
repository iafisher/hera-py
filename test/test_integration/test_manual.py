from hera.config import HERA_DATA_START
from hera.main import main
from hera.vm import VirtualMachine


def test_strings_program():
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
