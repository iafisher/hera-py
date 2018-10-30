import pytest

from hera.parser import Op, parse


def test_parse_setlo():
    assert parse('SETLO(R1, 4)') == [Op('SETLO', [1, 4])]


def test_parse_setlo_with_signed():
    assert parse('SETLO(R1, -12)') == [Op('SETLO', [1, -12])]


def test_parse_setlo_with_hex():
    assert parse('SETLO(R4, 0x5f)') == [Op('SETLO', [4, 0x5f])]


def test_parse_setlo_with_negative_hex():
    assert parse('SETLO(R7, -0x2B)') == [Op('SETLO', [7, -0x2b])]


def test_parse_several_ops():
    program = '''\
// Sets
SETLO(R1, 7)
SETHI(R2, -3)

// Logic
AND(R7, R8, R9)
OR(R7, R8, R9)
XOR(R7, R8, R9)

// Arithmetic
ADD(r3, r4, r5)
SUB(r3, r4, r5)
MUL(r3, r4, r5)

// Increment and decrement
INC(R2, 4)
DEC(R2, 12)

// Shifts
LSL(R1, 2)
LSR(R1, 2)
LSL8(R1, 2)
LSR8(R1, 2)
ASL(R1, 2)
ASR(R1, 2)

// Flags
SAVEF(R9)
RSTRF(R9)
FON(0x15)
FOFF(0x15)
FSET5(0x15)
FSET4(0x15)

// Memory
LOAD(R4, 0, R5)
STORE(R4, 0, R5)
'''
    oplist = parse(program)
    assert oplist == [
        Op('SETLO', [1, 7]),
        Op('SETHI', [2, -3]),
        Op('AND', [7, 8, 9]),
        Op('OR', [7, 8, 9]),
        Op('XOR', [7, 8, 9]),
        Op('ADD', [3, 4, 5]),
        Op('SUB', [3, 4, 5]),
        Op('MUL', [3, 4, 5]),
        Op('INC', [2, 4]),
        Op('DEC', [2, 12]),
        Op('LSL', [1, 2]),
        Op('LSR', [1, 2]),
        Op('LSL8', [1, 2]),
        Op('LSR8', [1, 2]),
        Op('ASL', [1, 2]),
        Op('ASR', [1, 2]),
        Op('SAVEF', [9]),
        Op('RSTRF', [9]),
        Op('FON', [0x15]),
        Op('FOFF', [0x15]),
        Op('FSET5', [0x15]),
        Op('FSET4', [0x15]),
        Op('LOAD', [4, 0, 5]),
        Op('STORE', [4, 0, 5]),
    ]


def test_parse_multiline_comment():
    program = '''\
/* Starts on this line
   ends on this one */
SETLO(R1, 1)
'''
    assert parse(program) == [Op('SETLO', [1, 1])]
