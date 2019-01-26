import pytest
from unittest.mock import patch

from hera.data import IntToken, Op, State, Token
from hera.op import ADD, CALL, INC, resolve_ops, SETHI, SETLO
from hera.parser import parse
from hera.typechecker import (
    Constant,
    DataLabel,
    get_labels,
    Label,
    operation_length,
    typecheck,
)


def R(s):
    return Token("REGISTER", s)


def SYM(s=""):
    return Token("SYMBOL", s)


def STR(s):
    return Token("STRING", s)


@pytest.fixture
def state():
    return State()


def helper(opstr, symbol_table={}):
    state = State()
    ops = resolve_ops(parse(opstr), state)
    if not ops or state.errors:
        return [(True, msg, loc) for msg, loc in state.errors]
    else:
        return ops[0].typecheck(symbol_table)


def valid(opstr, symbol_table={}):
    assert len(helper(opstr, symbol_table)) == 0


def invalid(opstr, msg, symbol_table={}):
    errors = helper(opstr, symbol_table)


def test_typecheck_SET():
    valid("SET(R1, 42)")
    valid("SET(R1, 0xFFFF)")
    valid("SET(R1, -0x7FFF)")


def test_typecheck_SETLO():
    valid("SETLO(R2, 42)")
    valid("SETLO(R2, 0xFF)")
    valid("SETLO(R2, -0x7F)")


def test_typecheck_SETHI():
    valid("SETHI(R2, 42)")
    valid("SETHI(R2, 0xFF)")
    valid("SETHI(R2, -0x7F)")


def test_typecheck_AND():
    valid("AND(R3, R4, R5)")


def test_typecheck_OR():
    valid("OR(R3, R4, R5)")


def test_typecheck_ADD():
    valid("ADD(R3, R4, R5)")


def test_typecheck_SUB():
    valid("SUB(R3, R4, R5)")


def test_typecheck_MUL():
    valid("MUL(R3, R4, R5)")


def test_typecheck_XOR():
    valid("XOR(R3, R4, R5)")


def test_typecheck_INC():
    valid("INC(R6, 42)")
    valid("INC(R6, 1)")
    valid("INC(R6, 64)")


def test_typecheck_DEC():
    valid("DEC(R6, 42)")
    valid("DEC(R6, 1)")
    valid("DEC(R6, 64)")


def test_typecheck_LSL():
    valid("LSL(R7, R8)")


def test_typecheck_LSR():
    valid("LSR(R7, R8)")


def test_typecheck_LSL8():
    valid("LSL8(R7, R8)")


def test_typecheck_LSR8():
    valid("LSR8(R7, R8)")


def test_typecheck_ASL():
    valid("ASL(R7, R8)")


def test_typecheck_ASR():
    valid("ASR(R7, R8)")


def test_typecheck_SAVEF():
    valid("SAVEF(R9)")


def test_typecheck_RSTRF():
    valid("RSTRF(R9)")


def test_typecheck_FON():
    valid("FON(0b10101)")
    valid("FON(0b01000)")
    valid("FON(0b11111)")
    valid("FON(0)")


def test_typecheck_FOFF():
    valid("FOFF(0b10101)")
    valid("FOFF(0b01000)")
    valid("FOFF(0b11111)")
    valid("FOFF(0)")


def test_typecheck_FSET5():
    valid("FSET5(0b10101)")
    valid("FSET5(0b01000)")
    valid("FSET5(0b11111)")
    valid("FSET5(0)")


def test_typecheck_FSET4():
    valid("FSET4(0b1010)")
    valid("FSET4(0b0100)")
    valid("FSET4(0b1111)")
    valid("FSET4(0)")


def test_typecheck_LOAD():
    valid("LOAD(R1, 0, R2)")
    valid("LOAD(R1, 0b11111, R2)")


def test_typecheck_STORE():
    valid("STORE(R1, 0, R2)")
    valid("STORE(R1, 0b11111, R2)")


def test_typecheck_CALL():
    valid("CALL(R12, R11)")
    valid("CALL(R12, f)", {"f": 0})


def test_typecheck_RETURN():
    valid("RETURN(R12, R13)")
    valid("RETURN(R12, f)", {"f": 0})


def test_typecheck_BR():
    valid("BR(R11)")
    valid("BR(l)", {"l": 0})


def test_typecheck_BRR():
    valid("BRR(0xFF)")
    valid("BRR(-0x7F)")


def test_typecheck_BL():
    valid("BL(R11)")
    valid("BL(l)", {"l": 0})


def test_typecheck_BLR():
    valid("BLR(0xFF)")
    valid("BLR(-0x7F)")


def test_typecheck_BGE():
    valid("BGE(R11)")
    valid("BGE(l)", {"l": 0})


def test_typecheck_BGER():
    valid("BGER(0xFF)")
    valid("BGER(-0x7F)")


def test_typecheck_BLE():
    valid("BLE(R11)")
    valid("BLE(l)", {"l": 0})


def test_typecheck_BLER():
    valid("BLER(0xFF)")
    valid("BLER(-0x7F)")


def test_typecheck_BG():
    valid("BG(R11)")
    valid("BG(l)", {"l": 0})


def test_typecheck_BGR():
    valid("BGR(0xFF)")
    valid("BGR(-0x7F)")


def test_typecheck_BULE():
    valid("BULE(R11)")
    valid("BULE(l)", {"l": 0})


def test_typecheck_BULER():
    valid("BULER(0xFF)")
    valid("BULER(-0x7F)")


def test_typecheck_BUG():
    valid("BUG(R11)")
    valid("BUG(l)", {"l": 0})


def test_typecheck_BUGR():
    valid("BUGR(0xFF)")
    valid("BUGR(-0x7F)")


def test_typecheck_BZ():
    valid("BZ(R11)")
    valid("BZ(l)", {"l": 0})


def test_typecheck_BZR():
    valid("BZR(0xFF)")
    valid("BZR(-0x7F)")


def test_typecheck_BNZ():
    valid("BNZ(R11)")
    valid("BNZ(l)", {"l": 0})


def test_typecheck_BNZR():
    valid("BNZR(0xFF)")
    valid("BNZR(-0x7F)")


def test_typecheck_BC():
    valid("BC(R11)")
    valid("BC(l)", {"l": 0})


def test_typecheck_BCR():
    valid("BCR(0xFF)")
    valid("BCR(-0x7F)")


def test_typecheck_BNC():
    valid("BNC(R11)")
    valid("BNC(l)", {"l": 0})


def test_typecheck_BNCR():
    valid("BNCR(0xFF)")
    valid("BNCR(-0x7F)")


def test_typecheck_BS():
    valid("BS(R11)")
    valid("BS(l)", {"l": 0})


def test_typecheck_BSR():
    valid("BSR(0xFF)")
    valid("BSR(-0x7F)")


def test_typecheck_BNS():
    valid("BNS(R11)")
    valid("BNS(l)", {"l": 0})


def test_typecheck_BNSR():
    valid("BNSR(0xFF)")
    valid("BNSR(-0x7F)")


def test_typecheck_BV():
    valid("BV(R11)")
    valid("BV(l)", {"l": 0})


def test_typecheck_BVR():
    valid("BVR(0xFF)")
    valid("BVR(-0x7F)")


def test_typecheck_BNV():
    valid("BNV(R11)")
    valid("BNV(l)", {"l": 0})


def test_typecheck_BNVR():
    valid("BNVR(0xFF)")
    valid("BNVR(-0x7F)")


def test_typecheck_SETRF():
    valid("SETRF(R1, 42)")
    valid("SETRF(R1, 0xFFFF)")
    valid("SETRF(R1, -0x7FFF)")


def test_typecheck_MOVE():
    valid("MOVE(R1, R2)")


def test_typecheck_CMP():
    valid("CMP(R1, R2)")


def test_typecheck_NEG():
    valid("NEG(R1, R2)")


def test_typecheck_NOT():
    valid("NOT(R1, R2)")


def test_typecheck_CBON():
    valid("CBON()")


def test_typecheck_CON():
    valid("CON()")


def test_typecheck_COFF():
    valid("COFF()")


def test_typecheck_CCBOFF():
    valid("CCBOFF()")


def test_typecheck_FLAGS():
    valid("FLAGS(R1)")


def test_typecheck_NOP():
    valid("NOP()")


def test_typecheck_HALT():
    valid("HALT()")


def test_typecheck_LABEL():
    valid("LABEL(l)")


def test_typecheck_CONSTANT():
    valid("CONSTANT(N, 0xFFFF)")
    valid("CONSTANT(N, -0x7FFF)")


def test_typecheck_DLABEL():
    valid("DLABEL(l)")


def test_typecheck_INTEGER():
    valid("INTEGER(0xFFFF)")
    valid("INTEGER(-0x7FFF)")


def test_typecheck_LP_STRING():
    valid('LP_STRING("hello!")')


def test_typecheck_TIGER_STRING():
    valid('TIGER_STRING("hello!")')


def test_typecheck_DSKIP():
    valid("DSKIP(0xFFFF)")
    valid("DSKIP(0)")


def test_typecheck_SWI():
    valid("SWI(0b1111)")
    valid("SWI(0b0110)")
    valid("SWI(0)")


def test_typecheck_RTI():
    valid("RTI()")


def test_typecheck_print_reg():
    valid("print_reg(R1)")


def test_typecheck_print():
    valid('print("hello, world!")')


def test_typecheck_println():
    valid('println("hello, world!")')


def test_typecheck___eval():
    valid("__eval(\"print('hello')\")")


def test_typecheck_undefined_symbol():
    invalid("SET(R1, N)", "undefined constant")


def test_typecheck_unknown_instruction():
    invalid("IF(R1)", "unknown instruction")


def test_typecheck_unknown_branch_instruction():
    invalid("BNWR(R1)", "unknown instruction")


def test_typecheck_single_error(state):
    # Second argument to SETHI is out of range.
    program = [SETLO(R("R1"), 10), SETHI(R("R1"), 1000)]
    symbol_table = typecheck(program, state)

    assert len(state.errors) == 1
    assert "integer must be in range [-128, 256)" in state.errors[0][0]


def test_typecheck_multiple_errors(state):
    program = [ADD(R("R1"), 10), INC(R("R3"))]
    symbol_table = typecheck(program, state)

    assert len(state.errors) == 3

    assert "ADD" in state.errors[0][0]
    assert "too few" in state.errors[0][0]

    assert "expected register" in state.errors[1][0]

    assert "INC" in state.errors[2][0]
    assert "too few" in state.errors[2][0]


def test_operation_length_of_register_branch_with_label():
    assert operation_length(Op("BNZ", [SYM("l")])) == 3


def test_operation_length_of_register_branch_with_register():
    assert operation_length(Op("BNZ", [R("R1")])) == 1


def test_operation_length_of_SET():
    assert operation_length(Op("SET", [R("R1"), 10])) == 2


def test_operation_length_of_SETRF():
    assert operation_length(Op("SETRF", [R("R1"), 10])) == 4


def test_operation_length_of_MOVE():
    assert operation_length(Op("MOVE", [R("R1"), R("R2")])) == 1


def test_operation_length_of_CMP():
    assert operation_length(Op("CMP", [R("R1"), R("R0")])) == 2


def test_operation_length_of_NEG():
    assert operation_length(Op("NEG", [R("R7"), R("R15")])) == 2


def test_operation_length_of_NOT():
    assert operation_length(Op("NOT", [R("R5"), R("R7")])) == 3


def test_operation_lentgh_of_FLAGS():
    assert operation_length(Op("FLAGS", [R("R3")])) == 2


def test_operation_length_of_CALL_with_label():
    assert operation_length(Op("CALL", [R("R12"), SYM("l")])) == 3


def test_operation_length_of_CALL_with_register():
    assert operation_length(Op("CALL", [R("R12"), R("R13")])) == 1


def test_get_labels_with_invalid_code(state):
    labels = get_labels([CALL(SYM("l"))], state)

    assert len(labels) == 0
    assert len(state.errors) == 0
