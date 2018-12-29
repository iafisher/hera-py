import pytest

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


def test_recursive_program(capsys):
    with pytest.raises(SystemExit):
        main(["test/assets/include/recursive.hera"])

    captured = capsys.readouterr()
    assert "recursive include" in captured.err
    assert '#include "recursive.hera"' in captured.err
    assert "line 1 of test/assets/include/recursive.hera" in captured.err


def test_mutually_recursive_programs(capsys):
    with pytest.raises(SystemExit):
        main(["test/assets/include/mutually_recursive1.hera"])

    captured = capsys.readouterr()
    assert "recursive include" in captured.err
    assert '#include "mutually_recursive1.hera"' in captured.err
    assert "line 1 of test/assets/include/mutually_recursive2.hera" in captured.err
