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


def test_include_stdin_program(capsys):
    program = '#include "-"\n#include "<stdin>"'
    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr()
    assert 'file "-" does not exist' in captured.err
    # We want this error and not a recursive include error, i.e. we need to distinguish
    # between actual standard input and a file called "<stdin>".
    assert 'file "<stdin>" does not exist' in captured.err


def test_use_of_ifdef(capsys):
    program = """\
SET(R1, 42)
#ifdef HERA_PY
SET(R2, 42)
#else
SET(R3, 666)
#endif

#ifdef HERA_C
R4 = 666;
#else
SET(R5, 42)
#endif

SET(R6, 42)
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == 42
    assert vm.registers[2] == 42
    assert vm.registers[3] == 0
    assert vm.registers[4] == 0
    assert vm.registers[5] == 42
    assert vm.registers[6] == 42


def test_use_of_ifdef_in_included_program(capsys):
    vm = execute_program_helper('#include "test/assets/include/ifdef.hera"')

    assert vm.registers[1] == 42
    assert vm.registers[2] == 42
    assert vm.registers[3] == 0
    assert vm.registers[4] == 0
    assert vm.registers[5] == 42
    assert vm.registers[6] == 42
