import pytest

from hera.main import main
from .utils import execute_program_helper


def test_basic_include():
    program = """\
#include "test/assets/include/lib/add.hera"

SET(R1, 20)
SET(R2, 22)
CALL(R12, add)
    """
    vm = execute_program_helper(program)

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


@pytest.mark.skip("not ready")
def test_multiple_includes():
    program = """\
#include "test/assets/include/lib/r1_to_42.hera"
#include "test/assets/include/lib/r2_to_42.hera"

SET(R3, 42)
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == 42
    assert vm.registers[2] == 42
    assert vm.registers[3] == 42


def test_recursive_program(capsys):
    with pytest.raises(SystemExit):
        main(["test/assets/include/recursive.hera"])

    captured = capsys.readouterr()
    assert "recursive include" in captured.err
    assert '#include "recursive.hera"' in captured.err
    assert "line 1 col 10 of test/assets/include/recursive.hera" in captured.err


def test_mutually_recursive_programs(capsys):
    with pytest.raises(SystemExit):
        main(["test/assets/include/mutually_recursive1.hera"])

    captured = capsys.readouterr()
    assert "recursive include" in captured.err
    assert '#include "mutually_recursive1.hera"' in captured.err
    assert (
        "line 1 col 10 of test/assets/include/mutually_recursive2.hera" in captured.err
    )


def test_nonexistent_path_program(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper('#include "test/assets/include/whatever.hera"')

    captured = capsys.readouterr()
    assert 'file "test/assets/include/whatever.hera" does not exist' in captured.err


@pytest.mark.skip("not ready")
def test_include_stdin_program(capsys):
    program = '#include "-"\n#include "<stdin>"'
    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr()
    assert 'file "test/assets/include/-" does not exist' in captured.err
    assert 'file "test/assets/include/<stdin>" does not exist' in captured.err
