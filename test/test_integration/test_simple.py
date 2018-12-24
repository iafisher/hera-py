from hera.main import main
from hera.symtab import HERA_DATA_START
from hera.vm import VirtualMachine


def test_addition_program(capsys):
    vm = VirtualMachine()
    main(["test/assets/simple/addition.hera"], vm)

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

    assert "Warning" not in capsys.readouterr().err


def test_loop_program(capsys):
    vm = VirtualMachine()
    main(["test/assets/simple/loop.hera"], vm)

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

    assert "Warning" not in capsys.readouterr().err


def test_function_call_program(capsys):
    vm = VirtualMachine()
    main(["test/assets/simple/function_call.hera"], vm)

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

    assert "Warning" not in capsys.readouterr().err


def test_fibonacci_program(capsys):
    vm = VirtualMachine()
    main(["test/assets/simple/fibonacci.hera"], vm)

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

    assert "Warning" not in capsys.readouterr().err


def test_data_easy_program(capsys):
    vm = VirtualMachine()
    main(["test/assets/simple/data_easy.hera"], vm)

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

    assert "Warning" not in capsys.readouterr().err


def test_dskip_program(capsys):
    vm = VirtualMachine()
    main(["test/assets/simple/dskip.hera"], vm)

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

    assert "Warning" not in capsys.readouterr().err


def test_loop_and_constant_program(capsys):
    vm = VirtualMachine()
    main(["test/assets/simple/loop_and_constant.hera"], vm)

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

    assert "Warning" not in capsys.readouterr().err


def test_hera_boilerplate_program():
    vm = VirtualMachine()
    main(["test/assets/simple/hera_boilerplate.hera"], vm)

    assert vm.registers[1] == 42
    assert vm.registers[2] == 42

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block
