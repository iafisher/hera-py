from unittest.mock import patch

from hera.data import IntToken, Op, Token
from hera.symtab import Constant, Label
from hera.typechecker import (
    assert_is_integer,
    assert_is_label,
    assert_is_register,
    assert_is_register_or_label,
    assert_is_string,
    assert_number_of_arguments,
    typecheck,
    typecheck_op,
)


def R(s):
    return Token("REGISTER", s)


def SYM(s=""):
    return Token("SYMBOL", s)


def STR(s):
    return Token("STRING", s)


def test_assert_number_of_arguments_with_too_few():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_number_of_arguments(Op("", [R("R1")]), 2)

        assert mock_emit_error.call_count == 1
        assert "too few" in mock_emit_error.call_args[0][0]


def test_assert_number_of_arguments_with_too_many():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_number_of_arguments(Op("", [R("R1"), R("R2")]), 1)

        assert mock_emit_error.call_count == 1
        assert "too many" in mock_emit_error.call_args[0][0]


def test_assert_is_register_with_valid_registers():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert assert_is_register(R("R1"))
        assert assert_is_register(R("R15"))
        assert assert_is_register(R("FP"))
        assert assert_is_register(R("SP"))
        assert assert_is_register(R("Rt"))
        assert assert_is_register(R("PC_ret"))
        assert assert_is_register(R("FP_alt"))

        assert mock_emit_error.call_count == 0


def test_assert_is_register_with_non_register_token():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_register("R1")
        assert not assert_is_register(10)

        assert mock_emit_error.call_count == 2
        assert "expected register" in mock_emit_error.call_args_list[0][0][0]
        assert "expected register" in mock_emit_error.call_args_list[1][0][0]


def test_assert_is_register_with_PC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_register(R("PC"))

        assert mock_emit_error.call_count == 1
        assert (
            "program counter cannot be accessed or changed directly"
            in mock_emit_error.call_args[0][0]
        )


def test_assert_is_register_with_invalid_register():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_register(R("R20"))

        assert mock_emit_error.call_count == 1
        assert "R20 is not a valid register" in mock_emit_error.call_args[0][0]


def test_assert_is_register_or_label_with_valid_registers():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert assert_is_register_or_label(R("R1"), {})
        assert assert_is_register_or_label(R("R15"), {})
        assert assert_is_register_or_label(R("FP"), {})
        assert assert_is_register_or_label(R("SP"), {})
        assert assert_is_register_or_label(R("Rt"), {})
        assert assert_is_register_or_label(R("PC_ret"), {})
        assert assert_is_register_or_label(R("FP_alt"), {})

        assert mock_emit_error.call_count == 0


def test_assert_is_register_or_label_with_non_register_token():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_register_or_label("R1", {})
        assert not assert_is_register_or_label(10, {})

        assert mock_emit_error.call_count == 2
        assert "expected register or label" in mock_emit_error.call_args_list[0][0][0]
        assert "expected register or label" in mock_emit_error.call_args_list[1][0][0]


def test_assert_is_register_or_label_with_PC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_register_or_label(R("PC"), {})

        assert mock_emit_error.call_count == 1
        assert (
            "program counter cannot be accessed or changed directly"
            in mock_emit_error.call_args[0][0]
        )


def test_assert_is_register_or_label_with_invalid_register():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_register_or_label(R("R20"), {})

        assert mock_emit_error.call_count == 1
        assert "R20 is not a valid register" in mock_emit_error.call_args[0][0]


def test_assert_is_register_or_label_with_defined_label():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert assert_is_register_or_label(SYM("n"), {"n": 10})

        assert mock_emit_error.call_count == 0


def test_assert_is_register_or_label_with_undefined_label():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_register_or_label(SYM("n"), {})

        assert mock_emit_error.call_count == 1
        assert "undefined symbol" in mock_emit_error.call_args[0][0]


def test_assert_is_label_with_valid_label():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert assert_is_label(SYM("l"))

        assert mock_emit_error.call_count == 0


def test_assert_is_label_with_non_label_token():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_label(R("R1"))

        assert mock_emit_error.call_count == 1
        assert "expected label" in mock_emit_error.call_args[0][0]


def test_assert_is_string_with_valid_string():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert assert_is_string(STR("hello"))

        assert mock_emit_error.call_count == 0


def test_assert_is_string_with_non_string_token():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_string(R("R1"))

        assert mock_emit_error.call_count == 1
        assert "expected string literal" in mock_emit_error.call_args[0][0]


def test_assert_is_integer_with_valid_integers():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert assert_is_integer(0, {}, bits=8, signed=False)
        assert assert_is_integer(17, {}, bits=8, signed=False)
        assert assert_is_integer(255, {}, bits=8, signed=False)

        assert assert_is_integer(0, {}, bits=16, signed=True)
        assert assert_is_integer(4000, {}, bits=16, signed=True)
        assert assert_is_integer(-4000, {}, bits=16, signed=True)
        assert assert_is_integer(65535, {}, bits=16, signed=True)
        assert assert_is_integer(-32768, {}, bits=16, signed=True)

        assert mock_emit_error.call_count == 0


def test_assert_is_integer_with_non_integer_token():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_integer(R("R1"), {}, bits=8, signed=True)

        assert mock_emit_error.call_count == 1
        assert "expected integer" in mock_emit_error.call_args[0][0]


def test_assert_is_integer_with_out_of_range_integers():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_integer(-1, {}, bits=8, signed=False)
        assert not assert_is_integer(256, {}, bits=8, signed=False)
        assert not assert_is_integer(-32769, {}, bits=16, signed=True)
        assert not assert_is_integer(65536, {}, bits=16, signed=True)
        assert not assert_is_integer(1000000, {}, bits=16, signed=True)

        args_list = mock_emit_error.call_args_list
        assert mock_emit_error.call_count == 5
        assert "integer must be in range [0, 256)" in args_list[0][0][0]
        assert "integer must be in range [0, 256)" in args_list[1][0][0]
        assert "integer must be in range [-32768, 65536)" in args_list[2][0][0]
        assert "integer must be in range [-32768, 65536)" in args_list[3][0][0]
        assert "integer must be in range [-32768, 65536)" in args_list[4][0][0]


def test_assert_is_integer_with_constant():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert assert_is_integer(SYM("n"), {"n": Constant(10)}, bits=16, signed=True)

        assert mock_emit_error.call_count == 0


def test_assert_is_integer_with_label():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert assert_is_integer(
            SYM("n"), {"n": Label(10)}, bits=16, signed=True, labels=True
        )

        assert mock_emit_error.call_count == 0


def test_assert_is_integer_with_disallowed_label():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_integer(SYM("n"), {"n": Label(10)}, bits=16, signed=True)

        assert mock_emit_error.call_count == 1
        assert "cannot use label as constant" in mock_emit_error.call_args[0][0]


def test_assert_is_integer_with_out_of_range_constant():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert not assert_is_integer(
            SYM("n"), {"n": Constant(1000)}, bits=8, signed=False
        )

        assert mock_emit_error.call_count == 1
        assert "integer must be in range [0, 256)" in mock_emit_error.call_args[0][0]


def test_typecheck_SET():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("SET", [R("R1"), 42]), {})
        assert typecheck_op(Op("SET", [R("R1"), 0xFFFF]), {})
        assert typecheck_op(Op("SET", [R("R1"), -0x7FFF]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SETLO():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("SETLO", [R("R2"), 42]), {})
        assert typecheck_op(Op("SETLO", [R("R2"), 0xFF]), {})
        assert typecheck_op(Op("SETLO", [R("R2"), -0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SETHI():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("SETHI", [R("R2"), 42]), {})
        assert typecheck_op(Op("SETHI", [R("R2"), 0xFF]), {})
        assert typecheck_op(Op("SETHI", [R("R2"), -0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_AND():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("AND", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_OR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("OR", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_ADD():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("ADD", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SUB():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("SUB", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_MUL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("MUL", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_XOR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("XOR", [R("R3"), R("R4"), R("R5")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_INC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("INC", [R("R6"), 42]), {})
        assert typecheck_op(Op("INC", [R("R6"), 1]), {})
        assert typecheck_op(Op("INC", [R("R6"), 64]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_DEC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("DEC", [R("R6"), 42]), {})
        assert typecheck_op(Op("DEC", [R("R6"), 1]), {})
        assert typecheck_op(Op("DEC", [R("R6"), 64]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LSL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("LSL", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LSR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("LSR", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LSL8():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("LSL8", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LSR8():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("LSR8", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_ASL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("ASL", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_ASR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("ASR", [R("R7"), R("R8")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SAVEF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("SAVEF", [R("R9")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_RSTRF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("RSTRF", [R("R9")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FON():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("FON", [0b10101]), {})
        assert typecheck_op(Op("FON", [0b01000]), {})
        assert typecheck_op(Op("FON", [0b11111]), {})
        assert typecheck_op(Op("FON", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FOFF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("FOFF", [0b10101]), {})
        assert typecheck_op(Op("FOFF", [0b01000]), {})
        assert typecheck_op(Op("FOFF", [0b11111]), {})
        assert typecheck_op(Op("FOFF", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FSET5():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("FSET5", [0b10101]), {})
        assert typecheck_op(Op("FSET5", [0b01000]), {})
        assert typecheck_op(Op("FSET5", [0b11111]), {})
        assert typecheck_op(Op("FSET5", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FSET4():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("FSET4", [0b1010]), {})
        assert typecheck_op(Op("FSET4", [0b0100]), {})
        assert typecheck_op(Op("FSET4", [0b1111]), {})
        assert typecheck_op(Op("FSET4", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LOAD():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("LOAD", [R("R1"), 0, R("R2")]), {})
        assert typecheck_op(Op("LOAD", [R("R1"), 0b11111, R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_STORE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("STORE", [R("R1"), 0, R("R2")]), {})
        assert typecheck_op(Op("STORE", [R("R1"), 0b11111, R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CALL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("CALL", [R("R12"), R("R11")]), {})
        assert typecheck_op(Op("CALL", [R("R12"), SYM("f")]), {"f": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_RETURN():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("RETURN", [R("R12"), R("R11")]), {})
        assert typecheck_op(Op("RETURN", [R("R12"), SYM("f")]), {"f": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BR", [R("R11")]), {})
        assert typecheck_op(Op("BR", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BRR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BRR", [0xFF]), {})
        assert typecheck_op(Op("BRR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BL", [R("R11")]), {})
        assert typecheck_op(Op("BL", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BLR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BLR", [0xFF]), {})
        assert typecheck_op(Op("BLR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BGE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BGE", [R("R11")]), {})
        assert typecheck_op(Op("BGE", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BGER():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BGER", [0xFF]), {})
        assert typecheck_op(Op("BGER", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BLE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BLE", [R("R11")]), {})
        assert typecheck_op(Op("BLE", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BLER():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BLER", [0xFF]), {})
        assert typecheck_op(Op("BLER", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BG():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BG", [R("R11")]), {})
        assert typecheck_op(Op("BG", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BGR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BGR", [0xFF]), {})
        assert typecheck_op(Op("BGR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BULE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BULE", [R("R11")]), {})
        assert typecheck_op(Op("BULE", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BULER():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BULER", [0xFF]), {})
        assert typecheck_op(Op("BULER", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BUG():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BUG", [R("R11")]), {})
        assert typecheck_op(Op("BUG", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BUGR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BUGR", [0xFF]), {})
        assert typecheck_op(Op("BUGR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BZ():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BZ", [R("R11")]), {})
        assert typecheck_op(Op("BZ", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BZR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BZR", [0xFF]), {})
        assert typecheck_op(Op("BZR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNZ():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BNZ", [R("R11")]), {})
        assert typecheck_op(Op("BNZ", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNZR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BNZR", [0xFF]), {})
        assert typecheck_op(Op("BNZR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BC", [R("R11")]), {})
        assert typecheck_op(Op("BC", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BCR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BCR", [0xFF]), {})
        assert typecheck_op(Op("BCR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNC():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BNC", [R("R11")]), {})
        assert typecheck_op(Op("BNC", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNCR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BNCR", [0xFF]), {})
        assert typecheck_op(Op("BNCR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BS():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BS", [R("R11")]), {})
        assert typecheck_op(Op("BS", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BSR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BSR", [0xFF]), {})
        assert typecheck_op(Op("BSR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNS():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BNS", [R("R11")]), {})
        assert typecheck_op(Op("BNS", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNSR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BNSR", [0xFF]), {})
        assert typecheck_op(Op("BNSR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BV():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BV", [R("R11")]), {})
        assert typecheck_op(Op("BV", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BVR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BVR", [0xFF]), {})
        assert typecheck_op(Op("BVR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNV():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BNV", [R("R11")]), {})
        assert typecheck_op(Op("BNV", [SYM("l")]), {"l": 0})
        assert mock_emit_error.call_count == 0


def test_typecheck_BNVR():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("BNVR", [0xFF]), {})
        assert typecheck_op(Op("BNVR", [-0x7F]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SETRF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("SETRF", [R("R1"), 42]), {})
        assert typecheck_op(Op("SETRF", [R("R1"), 0xFFFF]), {})
        assert typecheck_op(Op("SETRF", [R("R1"), -0x7FFF]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_MOVE():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("MOVE", [R("R1"), R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CMP():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("CMP", [R("R1"), R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_NEG():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("NEG", [R("R1"), R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_NOT():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("NOT", [R("R1"), R("R2")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CBON():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("CBON", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CON():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("CON", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_COFF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("COFF", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CCBOFF():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("CCBOFF", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_FLAGS():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("FLAGS", [R("R1")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_NOP():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("NOP", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_HALT():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("HALT", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LABEL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("LABEL", [SYM("l")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_CONSTANT():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("CONSTANT", [SYM("N"), 0xFFFF]), {})
        assert typecheck_op(Op("CONSTANT", [SYM("N"), -0x7FFF]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_DLABEL():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("DLABEL", [SYM("l")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_INTEGER():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("INTEGER", [0xFFFF]), {})
        assert typecheck_op(Op("INTEGER", [-0x7FFF]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_LP_STRING():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("LP_STRING", [Token("STRING", "hello!")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_DSKIP():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("DSKIP", [0xFFFF]), {})
        assert typecheck_op(Op("DSKIP", [0]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_SWI():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("SWI", [0b1111]), {})
        assert typecheck_op(Op("SWI", [0b0110]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_RTI():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("RTI", []), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_print_reg():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op("print_reg", [R("R1")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_print():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op(SYM("print"), [STR("hello, world!")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_println():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        assert typecheck_op(Op(SYM("println"), [STR("hello, world!")]), {})
        assert mock_emit_error.call_count == 0


def test_typecheck_undefined_symbol():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck_op(Op("SET", [R("R1"), SYM("N")]), {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "undefined constant" in mock_emit_error.call_args[0][0]


def test_typecheck_unknown_instruction():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck_op(Op("IF", [R("R1")]), {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "unknown instruction" in mock_emit_error.call_args[0][0]
        assert "IF" in mock_emit_error.call_args[0][0]


def test_typecheck_unknown_branch_instruction():
    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck_op(Op("BNWR", [R("R1")]), {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "unknown instruction" in mock_emit_error.call_args[0][0]
        assert "BNWR" in mock_emit_error.call_args[0][0]


def test_typecheck_single_error():
    # Second argument to SETHI is out of range.
    program = [Op("SETLO", [R("R1"), 10]), Op("SETHI", [R("R1"), 1000])]

    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck(program, {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "integer must be in range [-128, 256)" in mock_emit_error.call_args[0][0]


def test_typecheck_multiple_errors():
    program = [Op("ADD", [R("R1"), 10]), Op("INC", [R("R3")])]

    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck(program, {})

        assert not error_free
        assert mock_emit_error.call_count == 3

        call_args = mock_emit_error.call_args_list[0][0]
        assert "ADD" in call_args[0]
        assert "too few" in call_args[0]

        call_args = mock_emit_error.call_args_list[1][0]
        assert "expected register" in call_args[0]

        call_args = mock_emit_error.call_args_list[2][0]
        assert "INC" in call_args[0]
        assert "too few" in call_args[0]


def test_typecheck_data_statement_after_instruction():
    program = [Op("SET", [R("R1"), 42]), Op("DLABEL", [SYM("N")])]

    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck(program, {})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "data statement after instruction" in mock_emit_error.call_args[0][0]


def test_typecheck_relative_branch_with_label():
    program = [Op("BRR", [SYM("l")])]

    with patch("hera.utils._emit_msg") as mock_emit_error:
        error_free = typecheck(program, {"l": 7})

        assert not error_free
        assert mock_emit_error.call_count == 1
        assert "relative branches cannot use labels" in mock_emit_error.call_args[0][0]
        assert "why not use BR instead" in mock_emit_error.call_args[0][0]
