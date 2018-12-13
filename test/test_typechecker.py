import pytest

from lark import Token

from hera.parser import Op
from hera.typechecker import (
    check_types,
    LABEL,
    REGISTER,
    REGISTER_OR_LABEL,
    typecheck,
    typecheck_one,
    U4,
    U16,
)
from hera.utils import HERAError, IntToken


def R(s):
    return Token("REGISTER", s)


def SYM(s=""):
    return Token("SYMBOL", s)


def test_check_types_with_too_few():
    errors = check_types(SYM(), [REGISTER, REGISTER], [R("R1")])
    assert len(errors) == 1
    assert "too few" in errors[0].msg


def test_check_types_with_too_many():
    errors = check_types(SYM(), [REGISTER], [R("R1"), IntToken(10)])
    assert len(errors) == 1
    assert "too many" in errors[0].msg


def test_check_types_with_wrong_type():
    errors = check_types(SYM(), [REGISTER], [IntToken(10)])
    assert len(errors) == 1
    assert "not a register" in errors[0].msg

    errors2 = check_types(SYM(), [U16], [R("R1")])
    assert len(errors2) == 1
    assert "not an integer" in errors2[0].msg


def test_check_types_with_u16_out_of_range():
    errors = check_types(SYM(), [U16], [IntToken(65536)])
    assert len(errors) == 1
    assert "out of range" in errors[0].msg


def test_check_types_with_negative_u16():
    errors = check_types(SYM(), [U16], [IntToken(-1)])
    assert len(errors) == 1
    assert "must not be negative" in errors[0].msg


def test_check_types_with_u4_out_of_range():
    errors = check_types(SYM(), [U4], [IntToken(16)])
    assert len(errors) == 1
    assert "out of range" in errors[0].msg

    errors2 = check_types(SYM(), [U4], [IntToken(-1)])
    assert len(errors2) == 1
    assert "must not be negative" in errors2[0].msg


def test_check_types_with_range_object():
    errors = check_types(SYM(), [range(-10, 10)], [IntToken(-11)])
    assert len(errors) == 1
    assert "out of range" in errors[0].msg

    errors2 = check_types(SYM(), [range(-10, 10)], [IntToken(10)])
    assert len(errors2) == 1
    assert "out of range" in errors2[0].msg

    errors3 = check_types(SYM(), [range(-10, 10)], [R("R1")])
    assert len(errors3) == 1
    assert "not an integer" in errors3[0].msg

    r = range(-10, 10)
    assert check_types("", [r, r, r], [5, -10, 9]) == []


def test_check_types_with_constant_symbol():
    assert check_types("", [range(0, 100)], [Token("SYMBOL", "n")]) == []


def test_check_types_with_register_or_label():
    assert check_types("", [REGISTER_OR_LABEL], [Token("SYMBOL", "n")]) == []
    assert check_types("", [REGISTER_OR_LABEL], [R("R1")]) == []


def test_check_types_with_label():
    assert check_types("", [LABEL], [Token("SYMBOL", "n")]) == []


def test_typecheck_SET():
    assert typecheck_one(Op("SET", [R("R1"), 42])) == []
    assert typecheck_one(Op("SET", [R("R1"), 0xFFFF])) == []
    assert typecheck_one(Op("SET", [R("R1"), -0x7FFF])) == []


def test_typecheck_SETLO():
    assert typecheck_one(Op("SETLO", [R("R2"), 42])) == []
    assert typecheck_one(Op("SETLO", [R("R2"), 0xFF])) == []
    assert typecheck_one(Op("SETLO", [R("R2"), -0x7F])) == []


def test_typecheck_SETHI():
    assert typecheck_one(Op("SETHI", [R("R2"), 42])) == []
    assert typecheck_one(Op("SETHI", [R("R2"), 0xFF])) == []
    assert typecheck_one(Op("SETHI", [R("R2"), -0x7F])) == []


def test_typecheck_AND():
    assert typecheck_one(Op("AND", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_OR():
    assert typecheck_one(Op("OR", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_ADD():
    assert typecheck_one(Op("ADD", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_SUB():
    assert typecheck_one(Op("SUB", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_MUL():
    assert typecheck_one(Op("MUL", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_XOR():
    assert typecheck_one(Op("XOR", [R("R3"), R("R4"), R("R5")])) == []


def test_typecheck_INC():
    assert typecheck_one(Op("INC", [R("R6"), 42])) == []
    assert typecheck_one(Op("INC", [R("R6"), 1])) == []
    assert typecheck_one(Op("INC", [R("R6"), 64])) == []


def test_typecheck_DEC():
    assert typecheck_one(Op("DEC", [R("R6"), 42])) == []
    assert typecheck_one(Op("DEC", [R("R6"), 1])) == []
    assert typecheck_one(Op("DEC", [R("R6"), 64])) == []


def test_typecheck_LSL():
    assert typecheck_one(Op("LSL", [R("R7"), R("R8")])) == []


def test_typecheck_LSR():
    assert typecheck_one(Op("LSR", [R("R7"), R("R8")])) == []


def test_typecheck_LSL8():
    assert typecheck_one(Op("LSL8", [R("R7"), R("R8")])) == []


def test_typecheck_LSR8():
    assert typecheck_one(Op("LSR8", [R("R7"), R("R8")])) == []


def test_typecheck_ASL():
    assert typecheck_one(Op("ASL", [R("R7"), R("R8")])) == []


def test_typecheck_ASR():
    assert typecheck_one(Op("ASR", [R("R7"), R("R8")])) == []


def test_typecheck_SAVEF():
    assert typecheck_one(Op("SAVEF", [R("R9")])) == []


def test_typecheck_RSTRF():
    assert typecheck_one(Op("RSTRF", [R("R9")])) == []


def test_typecheck_FON():
    assert typecheck_one(Op("FON", [0b10101])) == []
    assert typecheck_one(Op("FON", [0b01000])) == []
    assert typecheck_one(Op("FON", [0b11111])) == []
    assert typecheck_one(Op("FON", [0])) == []


def test_typecheck_FOFF():
    assert typecheck_one(Op("FOFF", [0b10101])) == []
    assert typecheck_one(Op("FOFF", [0b01000])) == []
    assert typecheck_one(Op("FOFF", [0b11111])) == []
    assert typecheck_one(Op("FOFF", [0])) == []


def test_typecheck_FSET5():
    assert typecheck_one(Op("FSET5", [0b10101])) == []
    assert typecheck_one(Op("FSET5", [0b01000])) == []
    assert typecheck_one(Op("FSET5", [0b11111])) == []
    assert typecheck_one(Op("FSET5", [0])) == []


def test_typecheck_FSET4():
    assert typecheck_one(Op("FSET4", [0b1010])) == []
    assert typecheck_one(Op("FSET4", [0b0100])) == []
    assert typecheck_one(Op("FSET4", [0b1111])) == []
    assert typecheck_one(Op("FSET4", [0])) == []


def test_typecheck_LOAD():
    assert typecheck_one(Op("LOAD", [R("R1"), 0, R("R2")])) == []
    assert typecheck_one(Op("LOAD", [R("R1"), 0b11111, R("R2")])) == []


def test_typecheck_STORE():
    assert typecheck_one(Op("STORE", [R("R1"), 0, R("R2")])) == []
    assert typecheck_one(Op("STORE", [R("R1"), 0b11111, R("R2")])) == []


def test_typecheck_CALL():
    assert typecheck_one(Op("CALL", [R("R12"), R("R11")])) == []
    assert typecheck_one(Op("CALL", [R("R12"), SYM("f")])) == []


def test_typecheck_RETURN():
    assert typecheck_one(Op("RETURN", [R("R12"), R("R11")])) == []
    assert typecheck_one(Op("RETURN", [R("R12"), SYM("f")])) == []


def test_typecheck_BR():
    assert typecheck_one(Op("BR", [R("R11")])) == []
    assert typecheck_one(Op("BR", [SYM("l")])) == []


def test_typecheck_BRR():
    assert typecheck_one(Op("BRR", [0xFF])) == []
    assert typecheck_one(Op("BRR", [-0x7F])) == []


def test_typecheck_BL():
    assert typecheck_one(Op("BL", [R("R11")])) == []
    assert typecheck_one(Op("BL", [SYM("l")])) == []


def test_typecheck_BLR():
    assert typecheck_one(Op("BLR", [0xFF])) == []
    assert typecheck_one(Op("BLR", [-0x7F])) == []


def test_typecheck_BGE():
    assert typecheck_one(Op("BGE", [R("R11")])) == []
    assert typecheck_one(Op("BGE", [SYM("l")])) == []


def test_typecheck_BGER():
    assert typecheck_one(Op("BGER", [0xFF])) == []
    assert typecheck_one(Op("BGER", [-0x7F])) == []


def test_typecheck_BLE():
    assert typecheck_one(Op("BLE", [R("R11")])) == []
    assert typecheck_one(Op("BLE", [SYM("l")])) == []


def test_typecheck_BLER():
    assert typecheck_one(Op("BLER", [0xFF])) == []
    assert typecheck_one(Op("BLER", [-0x7F])) == []


def test_typecheck_BG():
    assert typecheck_one(Op("BG", [R("R11")])) == []
    assert typecheck_one(Op("BG", [SYM("l")])) == []


def test_typecheck_BGR():
    assert typecheck_one(Op("BGR", [0xFF])) == []
    assert typecheck_one(Op("BGR", [-0x7F])) == []


def test_typecheck_BULE():
    assert typecheck_one(Op("BULE", [R("R11")])) == []
    assert typecheck_one(Op("BULE", [SYM("l")])) == []


def test_typecheck_BULER():
    assert typecheck_one(Op("BULER", [0xFF])) == []
    assert typecheck_one(Op("BULER", [-0x7F])) == []


def test_typecheck_BUG():
    assert typecheck_one(Op("BUG", [R("R11")])) == []
    assert typecheck_one(Op("BUG", [SYM("l")])) == []


def test_typecheck_BUGR():
    assert typecheck_one(Op("BUGR", [0xFF])) == []
    assert typecheck_one(Op("BUGR", [-0x7F])) == []


def test_typecheck_BZ():
    assert typecheck_one(Op("BZ", [R("R11")])) == []
    assert typecheck_one(Op("BZ", [SYM("l")])) == []


def test_typecheck_BZR():
    assert typecheck_one(Op("BZR", [0xFF])) == []
    assert typecheck_one(Op("BZR", [-0x7F])) == []


def test_typecheck_BNZ():
    assert typecheck_one(Op("BNZ", [R("R11")])) == []
    assert typecheck_one(Op("BNZ", [SYM("l")])) == []


def test_typecheck_BNZR():
    assert typecheck_one(Op("BNZR", [0xFF])) == []
    assert typecheck_one(Op("BNZR", [-0x7F])) == []


def test_typecheck_BC():
    assert typecheck_one(Op("BC", [R("R11")])) == []
    assert typecheck_one(Op("BC", [SYM("l")])) == []


def test_typecheck_BCR():
    assert typecheck_one(Op("BCR", [0xFF])) == []
    assert typecheck_one(Op("BCR", [-0x7F])) == []


def test_typecheck_BNC():
    assert typecheck_one(Op("BNC", [R("R11")])) == []
    assert typecheck_one(Op("BNC", [SYM("l")])) == []


def test_typecheck_BNCR():
    assert typecheck_one(Op("BNCR", [0xFF])) == []
    assert typecheck_one(Op("BNCR", [-0x7F])) == []


def test_typecheck_BS():
    assert typecheck_one(Op("BS", [R("R11")])) == []
    assert typecheck_one(Op("BS", [SYM("l")])) == []


def test_typecheck_BSR():
    assert typecheck_one(Op("BSR", [0xFF])) == []
    assert typecheck_one(Op("BSR", [-0x7F])) == []


def test_typecheck_BNS():
    assert typecheck_one(Op("BNS", [R("R11")])) == []
    assert typecheck_one(Op("BNS", [SYM("l")])) == []


def test_typecheck_BNSR():
    assert typecheck_one(Op("BNSR", [0xFF])) == []
    assert typecheck_one(Op("BNSR", [-0x7F])) == []


def test_typecheck_BV():
    assert typecheck_one(Op("BV", [R("R11")])) == []
    assert typecheck_one(Op("BV", [SYM("l")])) == []


def test_typecheck_BVR():
    assert typecheck_one(Op("BVR", [0xFF])) == []
    assert typecheck_one(Op("BVR", [-0x7F])) == []


def test_typecheck_BNV():
    assert typecheck_one(Op("BNV", [R("R11")])) == []
    assert typecheck_one(Op("BNV", [SYM("l")])) == []


def test_typecheck_BNVR():
    assert typecheck_one(Op("BNVR", [0xFF])) == []
    assert typecheck_one(Op("BNVR", [-0x7F])) == []


def test_typecheck_SETRF():
    assert typecheck_one(Op("SETRF", [R("R1"), 42])) == []
    assert typecheck_one(Op("SETRF", [R("R1"), 0xFFFF])) == []
    assert typecheck_one(Op("SETRF", [R("R1"), -0x7FFF])) == []


def test_typecheck_MOVE():
    assert typecheck_one(Op("MOVE", [R("R1"), R("R2")])) == []


def test_typecheck_CMP():
    assert typecheck_one(Op("CMP", [R("R1"), R("R2")])) == []


def test_typecheck_NEG():
    assert typecheck_one(Op("NEG", [R("R1"), R("R2")])) == []


def test_typecheck_NOT():
    assert typecheck_one(Op("NOT", [R("R1"), R("R2")])) == []


def test_typecheck_CBON():
    assert typecheck_one(Op("CBON", [])) == []


def test_typecheck_CON():
    assert typecheck_one(Op("CON", [])) == []


def test_typecheck_COFF():
    assert typecheck_one(Op("COFF", [])) == []


def test_typecheck_CCBOFF():
    assert typecheck_one(Op("CCBOFF", [])) == []


def test_typecheck_FLAGS():
    assert typecheck_one(Op("FLAGS", [R("R1")])) == []


def test_typecheck_NOP():
    assert typecheck_one(Op("NOP", [])) == []


def test_typecheck_HALT():
    assert typecheck_one(Op("HALT", [])) == []


def test_typecheck_LABEL():
    assert typecheck_one(Op("LABEL", [SYM("l")])) == []


def test_typecheck_CONSTANT():
    assert typecheck_one(Op("CONSTANT", [SYM("N"), 0xFFFF])) == []
    assert typecheck_one(Op("CONSTANT", [SYM("N"), -0x7FFF])) == []


def test_typecheck_DLABEL():
    assert typecheck_one(Op("DLABEL", [SYM("l")])) == []


def test_typecheck_INTEGER():
    assert typecheck_one(Op("INTEGER", [0xFFFF])) == []
    assert typecheck_one(Op("INTEGER", [-0x7FFF])) == []


def test_typecheck_LP_STRING():
    assert typecheck_one(Op("LP_STRING", [Token("STRING", "hello!")])) == []


def test_typecheck_DSKIP():
    assert typecheck_one(Op("DSKIP", [0xFFFF])) == []
    assert typecheck_one(Op("DSKIP", [0])) == []


def test_typecheck_unknown_instruction():
    errors = typecheck_one(Op(SYM("IF"), [R("R1")]))
    assert len(errors) == 1
    assert "unknown instruction" in errors[0].msg
    assert "IF" in errors[0].msg


def test_typecheck_unknown_instruction():
    errors = typecheck_one(Op(SYM("IF"), [R("R1")]))
    assert len(errors) == 1
    assert "unknown instruction" in errors[0].msg
    assert "IF" in errors[0].msg


def test_typecheck_unknown_branch_instruction():
    errors = typecheck_one(Op(SYM("BNW"), [R("R1")]))
    assert len(errors) == 1
    assert "unknown instruction" in errors[0].msg
    assert "BNW" in errors[0].msg


def test_typecheck_single_error():
    # Second argument to SETHI is out of range.
    program = [
        Op(SYM("SETLO"), [R("R1"), IntToken(10)]),
        Op(SYM("SETHI"), [R("R1"), IntToken(1000)]),
    ]

    errors = typecheck(program)

    assert len(errors) == 1
    assert "SETHI" in errors[0].msg
    assert "out of range" in errors[0].msg


def test_typecheck_multiple_errors():
    program = [Op(SYM("ADD"), [R("R1"), IntToken(10)]), Op(SYM("INC"), [R("R3")])]

    errors = typecheck(program)

    assert len(errors) == 3

    assert "ADD" in errors[0].msg
    assert "too few" in errors[0].msg

    assert "ADD" in errors[1].msg
    assert "not a register" in errors[1].msg

    assert "INC" in errors[2].msg
    assert "too few" in errors[2].msg
