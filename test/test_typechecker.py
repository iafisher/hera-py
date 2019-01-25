import pytest
from unittest.mock import patch

from hera.data import IntToken, Op, State, Token
from hera.typechecker import (
    assert_is_integer,
    assert_is_label,
    assert_is_register,
    assert_is_register_or_label,
    assert_is_string,
    assert_number_of_arguments,
    Constant,
    DataLabel,
    Label,
    operation_length,
    typecheck,
    typecheck_op,
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


def test_assert_number_of_arguments_with_too_few(state):
    assert not assert_number_of_arguments(Op("", [R("R1")]), 2, state)

    assert len(state.errors) == 1
    assert "too few" in state.errors[0][0]


def test_assert_number_of_arguments_with_too_many(state):
    assert not assert_number_of_arguments(Op("", [R("R1"), R("R2")]), 1, state)

    assert len(state.errors) == 1
    assert "too many" in state.errors[0][0]


def test_assert_is_register_with_valid_registers(state):
    assert assert_is_register(R("R1"), state)
    assert assert_is_register(R("R15"), state)
    assert assert_is_register(R("FP"), state)
    assert assert_is_register(R("SP"), state)
    assert assert_is_register(R("Rt"), state)
    assert assert_is_register(R("PC_ret"), state)
    assert assert_is_register(R("FP_alt"), state)

    assert len(state.errors) == 0


def test_assert_is_register_with_non_register_token(state):
    assert not assert_is_register("R1", state)
    assert not assert_is_register(10, state)

    assert len(state.errors) == 2
    assert "expected register" in state.errors[0][0]
    assert "expected register" in state.errors[1][0]


def test_assert_is_register_with_PC(state):
    assert not assert_is_register(R("PC"), state)

    assert len(state.errors) == 1
    assert (
        "program counter cannot be accessed or changed directly" in state.errors[0][0]
    )


def test_assert_is_register_with_invalid_register(state):
    assert not assert_is_register(R("R20"), state)

    assert len(state.errors) == 1
    assert "R20 is not a valid register" in state.errors[0][0]


def test_assert_is_register_or_label_with_valid_registers(state):
    assert assert_is_register_or_label(R("R1"), {}, state)
    assert assert_is_register_or_label(R("R15"), {}, state)
    assert assert_is_register_or_label(R("FP"), {}, state)
    assert assert_is_register_or_label(R("SP"), {}, state)
    assert assert_is_register_or_label(R("Rt"), {}, state)
    assert assert_is_register_or_label(R("PC_ret"), {}, state)
    assert assert_is_register_or_label(R("FP_alt"), {}, state)

    assert len(state.errors) == 0


def test_assert_is_register_or_label_with_non_register_token(state):
    assert not assert_is_register_or_label("R1", {}, state)
    assert not assert_is_register_or_label(10, {}, state)

    assert len(state.errors) == 2
    assert "expected register or label" in state.errors[0][0]
    assert "expected register or label" in state.errors[1][0]


def test_assert_is_register_or_label_with_PC(state):
    assert not assert_is_register_or_label(R("PC"), {}, state)

    assert len(state.errors) == 1
    assert (
        "program counter cannot be accessed or changed directly" in state.errors[0][0]
    )


def test_assert_is_register_or_label_with_invalid_register(state):
    assert not assert_is_register_or_label(R("R20"), {}, state)

    assert len(state.errors) == 1
    assert "R20 is not a valid register" in state.errors[0][0]


def test_assert_is_register_or_label_with_defined_label(state):
    assert assert_is_register_or_label(SYM("n"), {"n": 10}, state)

    assert len(state.errors) == 0


def test_assert_is_register_or_label_with_undefined_label(state):
    assert not assert_is_register_or_label(SYM("n"), {}, state)

    assert len(state.errors) == 1
    assert "undefined symbol" in state.errors[0][0]


def test_assert_is_register_or_label_with_data_label(state):
    assert not assert_is_register_or_label(SYM("n"), {"n": DataLabel(16000)}, state)

    assert len(state.errors) == 1
    assert "data label cannot be used as branch label" in state.errors[0][0]


def test_assert_is_register_or_label_with_constant(state):
    assert not assert_is_register_or_label(SYM("n"), {"n": Constant(16000)}, state)

    assert len(state.errors) == 1
    assert "constant cannot be used as label" in state.errors[0][0]


def test_assert_is_label_with_valid_label(state):
    assert assert_is_label(SYM("l"), state)

    assert len(state.errors) == 0


def test_assert_is_label_with_non_label_token(state):
    assert not assert_is_label(R("R1"), state)

    assert len(state.errors) == 1
    assert "expected label" in state.errors[0][0]


def test_assert_is_string_with_valid_string(state):
    assert assert_is_string(STR("hello"), state)

    assert len(state.errors) == 0


def test_assert_is_string_with_non_string_token(state):
    assert not assert_is_string(R("R1"), state)

    assert len(state.errors) == 1
    assert "expected string literal" in state.errors[0][0]


def test_assert_is_integer_with_valid_integers(state):
    assert assert_is_integer(0, {}, state, bits=8, signed=False)
    assert assert_is_integer(17, {}, state, bits=8, signed=False)
    assert assert_is_integer(255, {}, state, bits=8, signed=False)

    assert assert_is_integer(0, {}, state, bits=16, signed=True)
    assert assert_is_integer(4000, {}, state, bits=16, signed=True)
    assert assert_is_integer(-4000, {}, state, bits=16, signed=True)
    assert assert_is_integer(65535, {}, state, bits=16, signed=True)
    assert assert_is_integer(-32768, {}, state, bits=16, signed=True)

    assert len(state.errors) == 0


def test_assert_is_integer_with_non_integer_token(state):
    assert not assert_is_integer(R("R1"), {}, state, bits=8, signed=True)

    assert len(state.errors) == 1
    assert "expected integer" in state.errors[0][0]


def test_assert_is_integer_with_out_of_range_integers(state):
    assert not assert_is_integer(-1, {}, state, bits=8, signed=False)
    assert not assert_is_integer(256, {}, state, bits=8, signed=False)
    assert not assert_is_integer(-32769, {}, state, bits=16, signed=True)
    assert not assert_is_integer(65536, {}, state, bits=16, signed=True)
    assert not assert_is_integer(1000000, {}, state, bits=16, signed=True)

    assert len(state.errors) == 5
    assert "integer must be in range [0, 256)" in state.errors[0][0]
    assert "integer must be in range [0, 256)" in state.errors[1][0]
    assert "integer must be in range [-32768, 65536)" in state.errors[2][0]
    assert "integer must be in range [-32768, 65536)" in state.errors[3][0]
    assert "integer must be in range [-32768, 65536)" in state.errors[4][0]


def test_assert_is_integer_with_constant(state):
    assert assert_is_integer(SYM("n"), {"n": Constant(10)}, state, bits=16, signed=True)

    assert len(state.errors) == 0


def test_assert_is_integer_with_label(state):
    assert assert_is_integer(
        SYM("n"), {"n": Label(10)}, state, bits=16, signed=True, labels=True
    )

    assert len(state.errors) == 0


def test_assert_is_integer_with_disallowed_label(state):
    assert not assert_is_integer(
        SYM("n"), {"n": Label(10)}, state, bits=16, signed=True
    )

    assert len(state.errors) == 1
    assert "cannot use label as constant" in state.errors[0][0]


def test_assert_is_integer_with_out_of_range_constant(state):
    assert not assert_is_integer(
        SYM("n"), {"n": Constant(1000)}, state, bits=8, signed=False
    )

    assert len(state.errors) == 1
    assert "integer must be in range [0, 256)" in state.errors[0][0]


def test_typecheck_SET(state):
    assert typecheck_op(Op("SET", [R("R1"), 42]), {}, state)
    assert typecheck_op(Op("SET", [R("R1"), 0xFFFF]), {}, state)
    assert typecheck_op(Op("SET", [R("R1"), -0x7FFF]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_SETLO(state):
    assert typecheck_op(Op("SETLO", [R("R2"), 42]), {}, state)
    assert typecheck_op(Op("SETLO", [R("R2"), 0xFF]), {}, state)
    assert typecheck_op(Op("SETLO", [R("R2"), -0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_SETHI(state):
    assert typecheck_op(Op("SETHI", [R("R2"), 42]), {}, state)
    assert typecheck_op(Op("SETHI", [R("R2"), 0xFF]), {}, state)
    assert typecheck_op(Op("SETHI", [R("R2"), -0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_AND(state):
    assert typecheck_op(Op("AND", [R("R3"), R("R4"), R("R5")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_OR(state):
    assert typecheck_op(Op("OR", [R("R3"), R("R4"), R("R5")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_ADD(state):
    assert typecheck_op(Op("ADD", [R("R3"), R("R4"), R("R5")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_SUB(state):
    assert typecheck_op(Op("SUB", [R("R3"), R("R4"), R("R5")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_MUL(state):
    assert typecheck_op(Op("MUL", [R("R3"), R("R4"), R("R5")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_XOR(state):
    assert typecheck_op(Op("XOR", [R("R3"), R("R4"), R("R5")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_INC(state):
    assert typecheck_op(Op("INC", [R("R6"), 42]), {}, state)
    assert typecheck_op(Op("INC", [R("R6"), 1]), {}, state)
    assert typecheck_op(Op("INC", [R("R6"), 64]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_DEC(state):
    assert typecheck_op(Op("DEC", [R("R6"), 42]), {}, state)
    assert typecheck_op(Op("DEC", [R("R6"), 1]), {}, state)
    assert typecheck_op(Op("DEC", [R("R6"), 64]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_LSL(state):
    assert typecheck_op(Op("LSL", [R("R7"), R("R8")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_LSR(state):
    assert typecheck_op(Op("LSR", [R("R7"), R("R8")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_LSL8(state):
    assert typecheck_op(Op("LSL8", [R("R7"), R("R8")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_LSR8(state):
    assert typecheck_op(Op("LSR8", [R("R7"), R("R8")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_ASL(state):
    assert typecheck_op(Op("ASL", [R("R7"), R("R8")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_ASR(state):
    assert typecheck_op(Op("ASR", [R("R7"), R("R8")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_SAVEF(state):
    assert typecheck_op(Op("SAVEF", [R("R9")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_RSTRF(state):
    assert typecheck_op(Op("RSTRF", [R("R9")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_FON(state):
    assert typecheck_op(Op("FON", [0b10101]), {}, state)
    assert typecheck_op(Op("FON", [0b01000]), {}, state)
    assert typecheck_op(Op("FON", [0b11111]), {}, state)
    assert typecheck_op(Op("FON", [0]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_FOFF(state):
    assert typecheck_op(Op("FOFF", [0b10101]), {}, state)
    assert typecheck_op(Op("FOFF", [0b01000]), {}, state)
    assert typecheck_op(Op("FOFF", [0b11111]), {}, state)
    assert typecheck_op(Op("FOFF", [0]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_FSET5(state):
    assert typecheck_op(Op("FSET5", [0b10101]), {}, state)
    assert typecheck_op(Op("FSET5", [0b01000]), {}, state)
    assert typecheck_op(Op("FSET5", [0b11111]), {}, state)
    assert typecheck_op(Op("FSET5", [0]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_FSET4(state):
    assert typecheck_op(Op("FSET4", [0b1010]), {}, state)
    assert typecheck_op(Op("FSET4", [0b0100]), {}, state)
    assert typecheck_op(Op("FSET4", [0b1111]), {}, state)
    assert typecheck_op(Op("FSET4", [0]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_LOAD(state):
    assert typecheck_op(Op("LOAD", [R("R1"), 0, R("R2")]), {}, state)
    assert typecheck_op(Op("LOAD", [R("R1"), 0b11111, R("R2")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_STORE(state):
    assert typecheck_op(Op("STORE", [R("R1"), 0, R("R2")]), {}, state)
    assert typecheck_op(Op("STORE", [R("R1"), 0b11111, R("R2")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_CALL(state):
    assert typecheck_op(Op("CALL", [R("R12"), R("R11")]), {}, state)
    assert typecheck_op(Op("CALL", [R("R12"), SYM("f")]), {"f": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_RETURN(state):
    assert typecheck_op(Op("RETURN", [R("R12"), R("R11")]), {}, state)
    assert typecheck_op(Op("RETURN", [R("R12"), SYM("f")]), {"f": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BR(state):
    assert typecheck_op(Op("BR", [R("R11")]), {}, state)
    assert typecheck_op(Op("BR", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BRR(state):
    assert typecheck_op(Op("BRR", [0xFF]), {}, state)
    assert typecheck_op(Op("BRR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BL(state):
    assert typecheck_op(Op("BL", [R("R11")]), {}, state)
    assert typecheck_op(Op("BL", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BLR(state):
    assert typecheck_op(Op("BLR", [0xFF]), {}, state)
    assert typecheck_op(Op("BLR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BGE(state):
    assert typecheck_op(Op("BGE", [R("R11")]), {}, state)
    assert typecheck_op(Op("BGE", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BGER(state):
    assert typecheck_op(Op("BGER", [0xFF]), {}, state)
    assert typecheck_op(Op("BGER", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BLE(state):
    assert typecheck_op(Op("BLE", [R("R11")]), {}, state)
    assert typecheck_op(Op("BLE", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BLER(state):
    assert typecheck_op(Op("BLER", [0xFF]), {}, state)
    assert typecheck_op(Op("BLER", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BG(state):
    assert typecheck_op(Op("BG", [R("R11")]), {}, state)
    assert typecheck_op(Op("BG", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BGR(state):
    assert typecheck_op(Op("BGR", [0xFF]), {}, state)
    assert typecheck_op(Op("BGR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BULE(state):
    assert typecheck_op(Op("BULE", [R("R11")]), {}, state)
    assert typecheck_op(Op("BULE", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BULER(state):
    assert typecheck_op(Op("BULER", [0xFF]), {}, state)
    assert typecheck_op(Op("BULER", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BUG(state):
    assert typecheck_op(Op("BUG", [R("R11")]), {}, state)
    assert typecheck_op(Op("BUG", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BUGR(state):
    assert typecheck_op(Op("BUGR", [0xFF]), {}, state)
    assert typecheck_op(Op("BUGR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BZ(state):
    assert typecheck_op(Op("BZ", [R("R11")]), {}, state)
    assert typecheck_op(Op("BZ", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BZR(state):
    assert typecheck_op(Op("BZR", [0xFF]), {}, state)
    assert typecheck_op(Op("BZR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BNZ(state):
    assert typecheck_op(Op("BNZ", [R("R11")]), {}, state)
    assert typecheck_op(Op("BNZ", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BNZR(state):
    assert typecheck_op(Op("BNZR", [0xFF]), {}, state)
    assert typecheck_op(Op("BNZR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BC(state):
    assert typecheck_op(Op("BC", [R("R11")]), {}, state)
    assert typecheck_op(Op("BC", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BCR(state):
    assert typecheck_op(Op("BCR", [0xFF]), {}, state)
    assert typecheck_op(Op("BCR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BNC(state):
    assert typecheck_op(Op("BNC", [R("R11")]), {}, state)
    assert typecheck_op(Op("BNC", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BNCR(state):
    assert typecheck_op(Op("BNCR", [0xFF]), {}, state)
    assert typecheck_op(Op("BNCR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BS(state):
    assert typecheck_op(Op("BS", [R("R11")]), {}, state)
    assert typecheck_op(Op("BS", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BSR(state):
    assert typecheck_op(Op("BSR", [0xFF]), {}, state)
    assert typecheck_op(Op("BSR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BNS(state):
    assert typecheck_op(Op("BNS", [R("R11")]), {}, state)
    assert typecheck_op(Op("BNS", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BNSR(state):
    assert typecheck_op(Op("BNSR", [0xFF]), {}, state)
    assert typecheck_op(Op("BNSR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BV(state):
    assert typecheck_op(Op("BV", [R("R11")]), {}, state)
    assert typecheck_op(Op("BV", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BVR(state):
    assert typecheck_op(Op("BVR", [0xFF]), {}, state)
    assert typecheck_op(Op("BVR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_BNV(state):
    assert typecheck_op(Op("BNV", [R("R11")]), {}, state)
    assert typecheck_op(Op("BNV", [SYM("l")]), {"l": 0}, state)
    assert len(state.errors) == 0


def test_typecheck_BNVR(state):
    assert typecheck_op(Op("BNVR", [0xFF]), {}, state)
    assert typecheck_op(Op("BNVR", [-0x7F]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_SETRF(state):
    assert typecheck_op(Op("SETRF", [R("R1"), 42]), {}, state)
    assert typecheck_op(Op("SETRF", [R("R1"), 0xFFFF]), {}, state)
    assert typecheck_op(Op("SETRF", [R("R1"), -0x7FFF]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_MOVE(state):
    assert typecheck_op(Op("MOVE", [R("R1"), R("R2")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_CMP(state):
    assert typecheck_op(Op("CMP", [R("R1"), R("R2")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_NEG(state):
    assert typecheck_op(Op("NEG", [R("R1"), R("R2")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_NOT(state):
    assert typecheck_op(Op("NOT", [R("R1"), R("R2")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_CBON(state):
    assert typecheck_op(Op("CBON", []), {}, state)
    assert len(state.errors) == 0


def test_typecheck_CON(state):
    assert typecheck_op(Op("CON", []), {}, state)
    assert len(state.errors) == 0


def test_typecheck_COFF(state):
    assert typecheck_op(Op("COFF", []), {}, state)
    assert len(state.errors) == 0


def test_typecheck_CCBOFF(state):
    assert typecheck_op(Op("CCBOFF", []), {}, state)
    assert len(state.errors) == 0


def test_typecheck_FLAGS(state):
    assert typecheck_op(Op("FLAGS", [R("R1")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_NOP(state):
    assert typecheck_op(Op("NOP", []), {}, state)
    assert len(state.errors) == 0


def test_typecheck_HALT(state):
    assert typecheck_op(Op("HALT", []), {}, state)
    assert len(state.errors) == 0


def test_typecheck_LABEL(state):
    assert typecheck_op(Op("LABEL", [SYM("l")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_CONSTANT(state):
    assert typecheck_op(Op("CONSTANT", [SYM("N"), 0xFFFF]), {}, state)
    assert typecheck_op(Op("CONSTANT", [SYM("N"), -0x7FFF]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_DLABEL(state):
    assert typecheck_op(Op("DLABEL", [SYM("l")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_INTEGER(state):
    assert typecheck_op(Op("INTEGER", [0xFFFF]), {}, state)
    assert typecheck_op(Op("INTEGER", [-0x7FFF]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_LP_STRING(state):
    assert typecheck_op(Op("LP_STRING", [Token("STRING", "hello!")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_TIGER_STRING(state):
    assert typecheck_op(Op("TIGER_STRING", [Token("STRING", "hello!")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_DSKIP(state):
    assert typecheck_op(Op("DSKIP", [0xFFFF]), {}, state)
    assert typecheck_op(Op("DSKIP", [0]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_SWI(state):
    assert typecheck_op(Op("SWI", [0b1111]), {}, state)
    assert typecheck_op(Op("SWI", [0b0110]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_RTI(state):
    assert typecheck_op(Op("RTI", []), {}, state)
    assert len(state.errors) == 0


def test_typecheck_print_reg(state):
    assert typecheck_op(Op("print_reg", [R("R1")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_print(state):
    assert typecheck_op(Op(SYM("print"), [STR("hello, world!")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_println(state):
    assert typecheck_op(Op(SYM("println"), [STR("hello, world!")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck___eval(state):
    assert typecheck_op(Op(SYM("__eval"), [STR("print('hello')")]), {}, state)
    assert len(state.errors) == 0


def test_typecheck_undefined_symbol(state):
    typecheck_op(Op("SET", [R("R1"), SYM("N")]), {}, state)

    assert len(state.errors) == 1
    assert "undefined constant" in state.errors[0][0]


def test_typecheck_unknown_instruction(state):
    typecheck_op(Op("IF", [R("R1")]), {}, state)

    assert len(state.errors) == 1
    assert "unknown instruction" in state.errors[0][0]
    assert "IF" in state.errors[0][0]


def test_typecheck_unknown_branch_instruction(state):
    typecheck_op(Op("BNWR", [R("R1")]), {}, state)

    assert len(state.errors) == 1
    assert "unknown instruction" in state.errors[0][0]
    assert "BNWR" in state.errors[0][0]


def test_typecheck_single_error(state):
    # Second argument to SETHI is out of range.
    program = [Op("SETLO", [R("R1"), 10]), Op("SETHI", [R("R1"), 1000])]
    symbol_table = typecheck(program, state)

    assert len(state.errors) == 1
    assert "integer must be in range [-128, 256)" in state.errors[0][0]


def test_typecheck_multiple_errors(state):
    program = [Op("ADD", [R("R1"), 10]), Op("INC", [R("R3")])]
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
