import pytest
from unittest.mock import patch

from hera.data import IntToken, Op, Token
from hera.typechecker import (
    check_one_type,
    check_types,
    LABEL,
    REGISTER,
    REGISTER_OR_LABEL,
    STRING,
    SYMBOL,
    typecheck,
    typecheck_one,
    U4,
    U16,
)


def R(s):
    return Token("REGISTER", s)


def SYM(s=""):
    return Token("SYMBOL", s)


def STR(s):
    return Token("STRING", s)


def test_check_types_with_too_few():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = check_types(SYM(), [REGISTER, REGISTER], [R("R1")], {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "too few" in mock_emit_error.call_args[0][0]


def test_check_types_with_too_many():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = check_types(SYM(), [REGISTER], [R("R1"), IntToken(10)], {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "too many" in mock_emit_error.call_args[0][0]


def test_check_types_with_wrong_type():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = check_types(SYM(), [REGISTER], [IntToken(10)], {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "not a register" in mock_emit_error.call_args[0][0]

    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = check_types(SYM(), [U16], [R("R1")], {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "not an integer" in mock_emit_error.call_args[0][0]


def test_check_types_with_program_counter():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = check_types(SYM(), [REGISTER], [R("PC")], {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert (
            "program counter cannot be accessed or changed directly"
            in mock_emit_error.call_args[0][0]
        )


def test_check_one_type_with_u16_out_of_range():
    assert check_one_type(U16, IntToken(65536), {}) == "out of range"


def test_check_one_type_with_negative_u16():
    assert check_one_type(U16, IntToken(-1), {}) == "must not be negative"


def test_check_one_type_with_u4_out_of_range():
    assert check_one_type(U4, IntToken(16), {}) == "out of range"
    assert check_one_type(U4, IntToken(-1), {}) == "must not be negative"


def test_check_one_type_with_range_object():
    assert check_one_type(range(-10, 10), IntToken(-11), {}) == "out of range"
    assert check_one_type(range(-10, 10), IntToken(10), {}) == "out of range"
    assert check_one_type(range(-10, 10), R("R1"), {}) == "not an integer"

    assert check_one_type(range(-10, 10), 5, {}) is None
    assert check_one_type(range(-10, 10), -10, {}) is None
    assert check_one_type(range(-10, 10), 9, {}) is None


def test_check_one_type_with_constant_symbol():
    assert check_one_type(range(0, 100), SYM("n"), {"n": 42}) is None


def test_check_one_type_with_register_or_label():
    assert check_one_type(REGISTER_OR_LABEL, 5, {}) == "not a register or label"
    assert check_one_type(REGISTER_OR_LABEL, SYM("n"), {"n": 42}) is None
    assert check_one_type(REGISTER_OR_LABEL, R("R1"), {}) is None


def test_check_one_type_with_invalid_register():
    assert check_one_type(REGISTER, R("R17"), {}) == "not a valid register"


def test_check_one_type_with_label():
    assert check_one_type(LABEL, 10, {}) == "not a symbol"
    assert check_one_type(LABEL, SYM("n"), {"n": 42}) is None


def test_check_one_type_with_undefined_label():
    assert check_one_type(LABEL, SYM("n"), {}) == "is undefined label"
    assert check_one_type(REGISTER_OR_LABEL, SYM("n"), {}) == "is undefined label"


def test_check_one_type_with_string():
    assert check_one_type(STRING, 10, {}) == "not a string"
    assert check_one_type(STRING, Token("STRING", "hello"), {}) is None


def test_check_one_type_with_symbol():
    assert check_one_type(SYMBOL, 10, {}) == "not a symbol"
    assert check_one_type(SYMBOL, SYM("x"), {}) is None


def test_typecheck_SET():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("SET", [R("R1"), 42]), {})
        assert typecheck_one(Op("SET", [R("R1"), 0xFFFF]), {})
        assert typecheck_one(Op("SET", [R("R1"), -0x7FFF]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SETLO():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("SETLO", [R("R2"), 42]), {})
        assert typecheck_one(Op("SETLO", [R("R2"), 0xFF]), {})
        assert typecheck_one(Op("SETLO", [R("R2"), -0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SETHI():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("SETHI", [R("R2"), 42]), {})
        assert typecheck_one(Op("SETHI", [R("R2"), 0xFF]), {})
        assert typecheck_one(Op("SETHI", [R("R2"), -0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_AND():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("AND", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_OR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("OR", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_ADD():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("ADD", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SUB():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("SUB", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_MUL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("MUL", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_XOR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("XOR", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_INC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("INC", [R("R6"), 42]), {})
        assert typecheck_one(Op("INC", [R("R6"), 1]), {})
        assert typecheck_one(Op("INC", [R("R6"), 64]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_DEC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("DEC", [R("R6"), 42]), {})
        assert typecheck_one(Op("DEC", [R("R6"), 1]), {})
        assert typecheck_one(Op("DEC", [R("R6"), 64]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LSL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("LSL", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LSR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("LSR", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LSL8():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("LSL8", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LSR8():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("LSR8", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_ASL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("ASL", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_ASR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("ASR", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SAVEF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("SAVEF", [R("R9")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_RSTRF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("RSTRF", [R("R9")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FON():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("FON", [0b10101]), {})
        assert typecheck_one(Op("FON", [0b01000]), {})
        assert typecheck_one(Op("FON", [0b11111]), {})
        assert typecheck_one(Op("FON", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FOFF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("FOFF", [0b10101]), {})
        assert typecheck_one(Op("FOFF", [0b01000]), {})
        assert typecheck_one(Op("FOFF", [0b11111]), {})
        assert typecheck_one(Op("FOFF", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FSET5():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("FSET5", [0b10101]), {})
        assert typecheck_one(Op("FSET5", [0b01000]), {})
        assert typecheck_one(Op("FSET5", [0b11111]), {})
        assert typecheck_one(Op("FSET5", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FSET4():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("FSET4", [0b1010]), {})
        assert typecheck_one(Op("FSET4", [0b0100]), {})
        assert typecheck_one(Op("FSET4", [0b1111]), {})
        assert typecheck_one(Op("FSET4", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LOAD():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("LOAD", [R("R1"), 0, R("R2")]), {})
        assert typecheck_one(Op("LOAD", [R("R1"), 0b11111, R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_STORE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("STORE", [R("R1"), 0, R("R2")]), {})
        assert typecheck_one(Op("STORE", [R("R1"), 0b11111, R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CALL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("CALL", [R("R12"), R("R11")]), {})
        assert typecheck_one(Op("CALL", [R("R12"), SYM("f")]), {"f": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_RETURN():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("RETURN", [R("R12"), R("R11")]), {})
        assert typecheck_one(Op("RETURN", [R("R12"), SYM("f")]), {"f": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BR", [R("R11")]), {})
        assert typecheck_one(Op("BR", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BRR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BRR", [0xFF]), {})
        assert typecheck_one(Op("BRR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BL", [R("R11")]), {})
        assert typecheck_one(Op("BL", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BLR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BLR", [0xFF]), {})
        assert typecheck_one(Op("BLR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BGE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BGE", [R("R11")]), {})
        assert typecheck_one(Op("BGE", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BGER():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BGER", [0xFF]), {})
        assert typecheck_one(Op("BGER", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BLE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BLE", [R("R11")]), {})
        assert typecheck_one(Op("BLE", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BLER():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BLER", [0xFF]), {})
        assert typecheck_one(Op("BLER", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BG():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BG", [R("R11")]), {})
        assert typecheck_one(Op("BG", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BGR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BGR", [0xFF]), {})
        assert typecheck_one(Op("BGR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BULE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BULE", [R("R11")]), {})
        assert typecheck_one(Op("BULE", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BULER():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BULER", [0xFF]), {})
        assert typecheck_one(Op("BULER", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BUG():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BUG", [R("R11")]), {})
        assert typecheck_one(Op("BUG", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BUGR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BUGR", [0xFF]), {})
        assert typecheck_one(Op("BUGR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BZ():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BZ", [R("R11")]), {})
        assert typecheck_one(Op("BZ", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BZR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BZR", [0xFF]), {})
        assert typecheck_one(Op("BZR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNZ():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BNZ", [R("R11")]), {})
        assert typecheck_one(Op("BNZ", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNZR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BNZR", [0xFF]), {})
        assert typecheck_one(Op("BNZR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BC", [R("R11")]), {})
        assert typecheck_one(Op("BC", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BCR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BCR", [0xFF]), {})
        assert typecheck_one(Op("BCR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BNC", [R("R11")]), {})
        assert typecheck_one(Op("BNC", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNCR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BNCR", [0xFF]), {})
        assert typecheck_one(Op("BNCR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BS():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BS", [R("R11")]), {})
        assert typecheck_one(Op("BS", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BSR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BSR", [0xFF]), {})
        assert typecheck_one(Op("BSR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNS():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BNS", [R("R11")]), {})
        assert typecheck_one(Op("BNS", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNSR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BNSR", [0xFF]), {})
        assert typecheck_one(Op("BNSR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BV():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BV", [R("R11")]), {})
        assert typecheck_one(Op("BV", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BVR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BVR", [0xFF]), {})
        assert typecheck_one(Op("BVR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNV():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BNV", [R("R11")]), {})
        assert typecheck_one(Op("BNV", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNVR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("BNVR", [0xFF]), {})
        assert typecheck_one(Op("BNVR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SETRF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("SETRF", [R("R1"), 42]), {})
        assert typecheck_one(Op("SETRF", [R("R1"), 0xFFFF]), {})
        assert typecheck_one(Op("SETRF", [R("R1"), -0x7FFF]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_MOVE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("MOVE", [R("R1"), R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CMP():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("CMP", [R("R1"), R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_NEG():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("NEG", [R("R1"), R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_NOT():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("NOT", [R("R1"), R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CBON():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("CBON", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CON():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("CON", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_COFF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("COFF", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CCBOFF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("CCBOFF", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FLAGS():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("FLAGS", [R("R1")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_NOP():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("NOP", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_HALT():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("HALT", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LABEL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("LABEL", [SYM("l")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CONSTANT():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("CONSTANT", [SYM("N"), 0xFFFF]), {})
        assert typecheck_one(Op("CONSTANT", [SYM("N"), -0x7FFF]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_DLABEL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("DLABEL", [SYM("l")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_INTEGER():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("INTEGER", [0xFFFF]), {})
        assert typecheck_one(Op("INTEGER", [-0x7FFF]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LP_STRING():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("LP_STRING", [Token("STRING", "hello!")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_DSKIP():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("DSKIP", [0xFFFF]), {})
        assert typecheck_one(Op("DSKIP", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SWI():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("SWI", [0b1111]), {})
        assert typecheck_one(Op("SWI", [0b0110]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_RTI():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("RTI", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_print_reg():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op("print_reg", [R("R1")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_print():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op(SYM("print"), [STR("hello, world!")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_println():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_one(Op(SYM("println"), [STR("hello, world!")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_undefined_symbol():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck_one(Op(SYM("SET"), [R("R1"), SYM("N")]), {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "undefined constant" in mock_emit_error.call_args[0][0]


def test_typecheck_unknown_instruction():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck_one(Op(SYM("IF"), [R("R1")]), {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "unknown instruction" in mock_emit_error.call_args[0][0]
        assert "IF" in mock_emit_error.call_args[0][0]


def test_typecheck_unknown_branch_instruction():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck_one(Op(SYM("BNWR"), [R("R1")]), {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "unknown instruction" in mock_emit_error.call_args[0][0]
        assert "BNWR" in mock_emit_error.call_args[0][0]


def test_typecheck_single_error():
    # Second argument to SETHI is out of range.
    program = [
        Op(SYM("SETLO"), [R("R1"), IntToken(10)]),
        Op(SYM("SETHI"), [R("R1"), IntToken(1000)]),
    ]

    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck(program, {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "SETHI" in mock_emit_error.call_args[0][0]
        assert "out of range" in mock_emit_error.call_args[0][0]


def test_typecheck_multiple_errors():
    program = [Op(SYM("ADD"), [R("R1"), IntToken(10)]), Op(SYM("INC"), [R("R3")])]

    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck(program, {})

        assert not error_free
        assert mock_emit_error.call_count == 3

        call_args = mock_emit_error.call_args_list[0][0]
        assert "ADD" in call_args[0]
        assert "too few" in call_args[0]

        call_args = mock_emit_error.call_args_list[1][0]
        assert "ADD" in call_args[0]
        assert "not a register" in call_args[0]

        call_args = mock_emit_error.call_args_list[2][0]
        assert "INC" in call_args[0]
        assert "too few" in call_args[0]


def test_typecheck_data_statement_after_instruction():
    program = [Op("SET", [R("R1"), 42]), Op(SYM("DLABEL"), [SYM("N")])]

    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck(program, {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "data statement after instruction" in mock_emit_error.call_args[0][0]


def test_typecheck_relative_branch_with_label():
    program = [Op(SYM("BRR"), [SYM("l")])]

    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck(program, {"l": 7})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "relative branches cannot use labels" in mock_emit_error.call_args[0][0]
        assert "why not use BR instead" in mock_emit_error.call_args[0][0]
