"""All test programs in this module taken from the official HERA manual.

TODO: Check these results against HERA-C.
"""
from hera.config import HERA_DATA_START
from hera.utils import to_u16
from .utils import execute_program_helper


def test_single_precision_arithmetic():
    # Figure 4.1, p. 25
    program = """\
SET(R2, 15)
SET(R3, 17)
SET(R4, -3)

CBON()

ADD(R1, R2, R3)
SETLO(Rt, 7)
MUL(R1, Rt, R1)
SETLO(Rt, 4)
MUL(Rt, Rt, R4)
ADD(R1, R1, Rt)

SUB(R5, R4, R3)
"""
    vm = execute_program_helper(program)

    assert vm.registers[1] == 212
    assert vm.registers[2] == 15
    assert vm.registers[3] == 17
    assert vm.registers[4] == to_u16(-3)
    assert vm.registers[5] == to_u16(-20)

    assert vm.flag_carry_block
    assert vm.flag_carry
    assert not vm.flag_overflow
    assert not vm.flag_zero
    assert vm.flag_sign


def test_double_precision_arithmetic():
    # Figure 4.2, p. 27
    program = """\
SET(R3, 17)
SET(R4, 4000)
SET(R5, 2)
SET(R6, 50000)
SET(R7, 500)
SET(R8, 3000)

CCBOFF()

COFF()
ADD(R2, R4, R6)
ADD(R1, R3, R5)
COFF()
SET(Rt, 16960)
ADD(R2, R2, Rt)
SETLO(Rt, 15)
ADD(R1, R1, Rt)

CON()
SUB(R8, R8, R2)
SUB(R7, R7, R1)
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == 35
    assert vm.registers[2] == 5424
    assert vm.registers[3] == 17
    assert vm.registers[4] == 4000
    assert vm.registers[5] == 2
    assert vm.registers[6] == 50000
    assert vm.registers[7] == 464
    assert vm.registers[8] == 63112

    assert not vm.flag_carry_block
    assert vm.flag_carry
    assert not vm.flag_overflow
    assert not vm.flag_zero
    assert not vm.flag_sign


def test_branching():
    # Figure 5.1, p. 30
    program = """\
CBON()
SETLO(R1, 0xB6)

CMP(R1, R0)
BGER(3)
NEG(R1, R1)
LSR(R1, R1)
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == 37


def test_global_variables():
    # Figure 6.1, p. 32
    program = """\
DLABEL(Variables)
DLABEL(X)
  INTEGER(12)
DLABEL(Y)
  DSKIP(1)
DLABEL(Z)
  INTEGER(4)

CBON()

SET(Rt, X)
LOAD(R1, 0, Rt)
INC(R1, 5)
SET(Rt, Y)
STORE(R1, 0, Rt)

SET(R1, Variables)
LOAD(R2, 0, R1)
LOAD(R3, 1, R1)
ADD(R3, R3, R3)
ADD(R2, R2, R3)
LOAD(R3, 2, R1)
SUB(R2, R2, R3)
STORE(R2, 0, R1)

HALT()
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == HERA_DATA_START
    assert vm.registers[2] == 42
    assert vm.registers[3] == 4

    assert vm.memory[HERA_DATA_START] == 42
    assert vm.memory[HERA_DATA_START + 1] == 17
    assert vm.memory[HERA_DATA_START + 2] == 4


def test_arrays():
    # Figure 6.2, p. 34
    program = """\
DLABEL(ArrayOfSevenPrimes)
  INTEGER(7)
  INTEGER(2) INTEGER(3) INTEGER(5) INTEGER(7) DSKIP(1) INTEGER(13) INTEGER(17)
DLABEL(ArrayOfSevenSquaredPrimes)
  DSKIP(8)

  CBON()

  SET(Rt, ArrayOfSevenPrimes)
  SETLO(R1, 5)
  ADD(Rt, Rt, R1)
  SETLO(R1, 11)
  STORE(R1, 0, Rt)

  SET(R1, ArrayOfSevenPrimes)
  SET(R2, ArrayOfSevenSquaredPrimes)
  LOAD(R3, 0, R1)
  STORE(R3, 0, R2)

LABEL(SquareNextOne)
  DEC(R3, 1)
BL(NoMoreSquares)
  INC(R1, 1)
  INC(R2, 1)
  LOAD(R4, 0, R1)
  MUL(R4, R4, R4)
  STORE(R4, 0, R2)
BR(SquareNextOne)

LABEL(NoMoreSquares)
HALT()
    """
    vm = execute_program_helper(program)

    assert vm.registers[1] == HERA_DATA_START + 7
    assert vm.registers[2] == HERA_DATA_START + 15
    assert vm.registers[3] == to_u16(-1)
    assert vm.registers[4] == 289

    assert vm.memory[HERA_DATA_START] == 7
    assert vm.memory[HERA_DATA_START + 1] == 2
    assert vm.memory[HERA_DATA_START + 2] == 3
    assert vm.memory[HERA_DATA_START + 3] == 5
    assert vm.memory[HERA_DATA_START + 4] == 7
    assert vm.memory[HERA_DATA_START + 5] == 11
    assert vm.memory[HERA_DATA_START + 6] == 13
    assert vm.memory[HERA_DATA_START + 7] == 17

    assert vm.memory[HERA_DATA_START + 8] == 7
    assert vm.memory[HERA_DATA_START + 9] == 4
    assert vm.memory[HERA_DATA_START + 10] == 9
    assert vm.memory[HERA_DATA_START + 11] == 25
    assert vm.memory[HERA_DATA_START + 12] == 49
    assert vm.memory[HERA_DATA_START + 13] == 121
    assert vm.memory[HERA_DATA_START + 14] == 169
    assert vm.memory[HERA_DATA_START + 15] == 289


def test_strings():
    # Figure 6.3, p. 35
    program = """\
DLABEL(The_string)
  LP_STRING("Is this an example? With three questions? Really?")

DLABEL(N_questions)
  INTEGER(0)

CBON()
SET(R1, 0)
SET(R2, The_string)
LOAD(R3, 0, R2)
INC(R2, 1)

LABEL(top_of_loop)
  LOAD(R4, 0, R2)
  SET(R5, 63)
  SUB(R0, R4, R5)
BNZ(not_a_question)
  INC(R1, 1)
LABEL(not_a_question)
  INC(R2, 1)
  DEC(R3, 1)
BNZ(top_of_loop)

SET(R2, N_questions)
STORE(R1, 0, R2)
HALT()
    """
    vm = execute_program_helper(program)

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
