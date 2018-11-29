import pytest

from lark import Token

from hera.parser import Op
from hera.preprocessor import (
    convert,
    convert_set,
    get_labels,
    preprocess,
    verify_args,
    HERA_DATA_START,
    REGISTER,
    REGISTER_OR_LABEL,
    U4,
    U16,
)
from hera.utils import HERAError, IntToken


def R(s):
    return Token("REGISTER", s)


def test_convert_set_with_small_positive():
    assert convert_set("R5", 18) == [Op("SETLO", ["R5", 18])]


def test_convert_set_with_large_positive():
    assert convert_set("R5", 34000) == [
        Op("SETLO", ["R5", 208]),
        Op("SETHI", ["R5", 132]),
    ]


def test_convert_set_with_negative():
    assert convert_set("R5", -5) == [
        Op("SETLO", ["R5", 251]),
        Op("SETHI", ["R5", 255]),
    ]


def test_convert_set_with_symbol():
    assert convert_set("R5", "whatever") == [
        Op("SETLO", ["R5", "whatever"]),
        Op("SETHI", ["R5", "whatever"]),
    ]


def test_convert_move():
    assert convert(Op("MOVE", ["R5", "R3"])) == [Op("OR", ["R5", "R3", "R0"])]


def test_convert_con():
    assert convert(Op("CON", [])) == [Op("FON", [8])]


def test_convert_coff():
    assert convert(Op("COFF", [])) == [Op("FOFF", [8])]


def test_convert_cbon():
    assert convert(Op("CBON", [])) == [Op("FON", [16])]


def test_convert_ccboff():
    assert convert(Op("CCBOFF", [])) == [Op("FOFF", [24])]


def test_convert_cmp():
    assert convert(Op("CMP", ["R1", "R2"])) == [
        Op("FON", [8]),
        Op("SUB", ["R0", "R1", "R2"]),
    ]


def test_convert_setrf_with_small_positive():
    assert convert(Op("SETRF", ["R5", 18])) == [
        Op("SETLO", ["R5", 18]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_convert_setrf_with_large_positive():
    assert convert(Op("SETRF", ["R5", 34000])) == [
        Op("SETLO", ["R5", 208]),
        Op("SETHI", ["R5", 132]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_convert_setrf_with_negative():
    assert convert(Op("SETRF", ["R5", -5])) == [
        Op("SETLO", ["R5", 251]),
        Op("SETHI", ["R5", 255]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_convert_flags():
    assert convert(Op("FLAGS", ["R8"])) == [Op("FOFF", [8]), Op("ADD", ["R0", "R8", "R0"])]


def test_convert_halt():
    assert convert(Op("HALT", [])) == [Op("BRR", [0])]


def test_convert_nop():
    assert convert(Op("NOP", [])) == [Op("BRR", [1])]


def test_convert_call_with_register():
    assert convert(Op("CALL", ["R12", R("R13")])) == [Op("CALL", ["R12", "R13"])]


def test_convert_call_with_label():
    assert convert(Op("CALL", ["R12", Token("SYMBOL", "div")])) == [
        Op("SETLO", ["R13", "div"]),
        Op("SETHI", ["R13", "div"]),
        Op("CALL", ["R12", "R13"]),
    ]


def test_convert_neg():
    assert convert(Op("NEG", ["R1", "R2"])) == [
        Op("FON", [8]),
        Op("SUB", ["R1", "R0", "R2"]),
    ]


def test_convert_not():
    assert convert(Op("NOT", ["R1", "R2"])) == [
        Op("SETLO", ["R11", 0xFF]),
        Op("SETHI", ["R11", 0xFF]),
        Op("XOR", ["R1", "R11", "R2"]),
    ]


def test_get_labels_with_example():
    labels = get_labels(
        [
            Op("DLABEL", ["data"]),
            Op("INTEGER", [42]),
            Op("INTEGER", [43]),
            Op("DLABEL", ["data2"]),
            Op("INTEGER", [100]),
            Op("LABEL", ["top"]),
            Op("ADD", ["R0", "R0", "R0"]),
            Op("LABEL", ["bottom"]),
        ]
    )
    assert len(labels) == 4
    assert labels["data"] == HERA_DATA_START
    assert labels["data2"] == HERA_DATA_START + 2
    assert labels["top"] == 0
    assert labels["bottom"] == 1


def test_get_labels_with_dskip():
    labels = get_labels(
        [
            Op("DLABEL", ["data"]),
            Op("INTEGER", [42]),
            Op("DSKIP", [10]),
            Op("DLABEL", ["data2"]),
            Op("INTEGER", [84]),
        ]
    )
    assert len(labels) == 2
    assert labels["data"] == HERA_DATA_START
    assert labels["data2"] == HERA_DATA_START + 11


def test_get_labels_with_lp_string():
    labels = get_labels(
        [
            Op("DLABEL", ["S"]),
            Op("LP_STRING", ["hello"]),
            Op("DLABEL", ["X"]),
            Op("INTEGER", [42]),
        ]
    )
    assert len(labels) == 2
    assert labels["S"] == HERA_DATA_START
    assert labels["X"] == HERA_DATA_START + 6


def test_get_labels_with_empty_lp_string():
    labels = get_labels(
        [
            Op("DLABEL", ["S"]),
            Op("LP_STRING", [""]),
            Op("DLABEL", ["X"]),
            Op("INTEGER", [42]),
        ]
    )
    assert len(labels) == 2
    assert labels["S"] == HERA_DATA_START
    assert labels["X"] == HERA_DATA_START + 1


def test_preprocess_constant():
    program = [
        Op(Token("SYMBOL", "CONSTANT"), [Token("SYMBOL", "n"), IntToken(100)]),
        Op(Token("SYMBOL", "SET"), [R("R1"), Token("SYMBOL", "n")]),
    ]
    assert preprocess(program) == [Op("SETLO", ["R1", 100]), Op("SETHI", ["R1", 0])]


def test_verify_args_with_too_few():
    with pytest.raises(HERAError) as e:
        verify_args("", [REGISTER, REGISTER], [R("R1")])
    assert "too few" in str(e)


def test_verify_args_with_too_many():
    with pytest.raises(HERAError) as e:
        verify_args("", [REGISTER], [R("R1"), IntToken(10)])
    assert "too many" in str(e)


def test_verify_args_with_wrong_type():
    with pytest.raises(HERAError) as e1:
        verify_args("", [REGISTER], [IntToken(10)])
    assert "not a register" in str(e1)

    with pytest.raises(HERAError) as e2:
        verify_args("", [U16], [R("R1")])
    assert "not an integer" in str(e2)


def test_verify_args_with_u16_out_of_range():
    with pytest.raises(HERAError) as e:
        verify_args("", [U16], [IntToken(65536)])
    assert "out of range" in str(e)


def test_verify_args_with_negative_u16():
    with pytest.raises(HERAError) as e:
        verify_args("", [U16], [IntToken(-1)])
    assert "must not be negative" in str(e)


def test_verify_args_with_u4_out_of_range():
    with pytest.raises(HERAError) as e1:
        verify_args("", [U4], [IntToken(16)])
    assert "out of range" in str(e1)

    with pytest.raises(HERAError) as e2:
        verify_args("", [U4], [IntToken(-1)])
    assert "must not be negative" in str(e2)


def test_verify_args_with_range_object():
    with pytest.raises(HERAError) as e1:
        verify_args("", [range(-10, 10)], [IntToken(-11)])
    assert "out of range" in str(e1)

    with pytest.raises(HERAError) as e2:
        verify_args("", [range(-10, 10)], [IntToken(10)])
    assert "out of range" in str(e2)

    with pytest.raises(HERAError) as e3:
        verify_args("", [range(-10, 10)], [R("R1")])
    assert "not an integer" in str(e3)

    r = range(-10, 10)
    verify_args("", [r, r, r], [5, -10, 9])


def test_verify_args_with_constant_symbol():
    verify_args("", [range(0, 100)], [Token("SYMBOL", "n")])


def test_verify_args_with_register_or_label():
    verify_args("", [REGISTER_OR_LABEL], [Token("SYMBOL", "n")])
    verify_args("", [REGISTER_OR_LABEL], [R("R1")])
