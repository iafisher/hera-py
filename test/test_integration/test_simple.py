from hera.config import HERA_DATA_START
from .utils import execute_program_helper


def test_addition_program(capsys):
    program = """\
SET(R1, 20)
SET(R2, 22)
ADD(R3, R1, R2)
    """
    vm = execute_program_helper(program)

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
    program = """\
SET(R1, 1)
SET(R2, 10)
LABEL(top)
INC(R1, 1)
CMP(R1, R2)
BZ(bottom)
BR(top)
LABEL(bottom)
    """
    vm = execute_program_helper(program)

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
    program = """\
SET(R1, 8)
CALL(R12, times_two)
HALT()

// Multiply R1 by two, in-place
LABEL(times_two)
  LSL(R1, R1)
  RETURN(R12, Rt)
    """
    vm = execute_program_helper(program)

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
    # TODO: Does this really belong in the simple test suite?
    program = """\
/*

fib(n)
  i = 1
  fib_i = 1
  fib_i_minus_1 = 0
  while i < n
    tmp = fib_i
    fib_i = fib_i + fib_i_minus_1
    fib_i_minus_1 = fib_i
    i += 1
  return fib_i

*/

CBON()

// n = 12
SET(R1, 12)

// fib_i = 1
SET(R2, 1)
// fib_i_minus_1 = 0
SET(R3, 0)
// i = 1
SET(R4, 1)

LABEL(top)
CMP(R4, R1)
BZ(bottom)

// tmp = fib_i
MOVE(R5, R2)
ADD(R2, R2, R3)
MOVE(R3, R5)
INC(R4, 1)

BR(top)
LABEL(bottom)
    """
    vm = execute_program_helper(program)

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
    program = """\
DLABEL(X)
INTEGER(42)

SET(R1, X)
LOAD(R2, 0, R1)
    """
    vm = execute_program_helper(program)

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
    program = """\
DLABEL(first_array)
INTEGER(42)
DSKIP(10)
INTEGER(84)

SET(R1, first_array)
LOAD(R2, 0, R1)
LOAD(R3, 11, R1)
    """
    vm = execute_program_helper(program)

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
    program = """\
CONSTANT(N, 100)

SET(R1, N)
SET(R2, 0)
SET(R3, 0)

LABEL(top)
CMP(R1, R2)
BZ(bottom)
ADD(R3, R3, R2)
INC(R2, 1)
BR(top)
LABEL(bottom)
    """
    vm = execute_program_helper(program)

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
    program = """\
#include <HERA.h>

void HERA_main() {
   SET(R1, 42);
   SET(R2, 42)
}
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == 42
    assert vm.registers[2] == 42

    assert not vm.flag_sign
    assert not vm.flag_zero
    assert not vm.flag_overflow
    assert not vm.flag_carry
    assert not vm.flag_carry_block


def test_relative_branching():
    program = """\
SET(R1, 10)
SET(R2, 32)
BRR(after)
SET(R2, 656)
LABEL(after)
ADD(R3, R1, R2)
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == 10
    assert vm.registers[2] == 32
    assert vm.registers[3] == 42


def test_relative_branching_backwards():
    program = """\
BRR(after)
LABEL(before)
HALT()
LABEL(after)
SET(R1, 42)
BRR(before)
SET(R1, 666)
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == 42


def test_branching_by_register():
    program = """\
SET(R1, end)
SET(R2, 42)
BR(R1)

SET(R2, 666)
LABEL(end)
SET(R3, 84)
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == 7
    assert vm.registers[2] == 42
    assert vm.registers[3] == 84
