import pytest

from lark import Token

from hera.parser import Op
from hera.preprocessor import (
    preprocess,
    verify_args,
    Preprocessor,
    HERA_DATA_START,
    REGISTER,
    REGISTER_OR_LABEL,
    U4,
    U16,
)
from hera.utils import HERAError, IntToken


@pytest.fixture
def ppr():
    return Preprocessor()


def REG(s):
    return Token("REGISTER", s)


def test_convert_set_with_small_positive(ppr):
    assert ppr.convert_set("R5", 18) == [Op("SETLO", ["R5", 18])]


def test_convert_set_with_large_positive(ppr):
    assert ppr.convert_set("R5", 34000) == [
        Op("SETLO", ["R5", 208]),
        Op("SETHI", ["R5", 132]),
    ]


def test_convert_set_with_negative(ppr):
    assert ppr.convert_set("R5", -5) == [
        Op("SETLO", ["R5", 251]),
        Op("SETHI", ["R5", 255]),
    ]


def test_convert_set_with_symbol(ppr):
    assert ppr.convert_set("R5", "whatever") == [
        Op("SETLO", ["R5", "whatever"]),
        Op("SETHI", ["R5", "whatever"]),
    ]


def test_convert_move(ppr):
    assert ppr.convert_move("R5", "R3") == [Op("OR", ["R5", "R3", "R0"])]


def test_convert_con(ppr):
    assert ppr.convert_con() == [Op("FON", [8])]


def test_convert_coff(ppr):
    assert ppr.convert_coff() == [Op("FOFF", [8])]


def test_convert_cbon(ppr):
    assert ppr.convert_cbon() == [Op("FON", [16])]


def test_convert_ccboff(ppr):
    assert ppr.convert_ccboff() == [Op("FOFF", [24])]


def test_convert_cmp(ppr):
    assert ppr.convert_cmp("R1", "R2") == [
        Op("FON", [8]),
        Op("SUB", ["R0", "R1", "R2"]),
    ]


def test_convert_setrf_with_small_positive(ppr):
    assert ppr.convert_setrf("R5", 18) == [
        Op("SETLO", ["R5", 18]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_convert_setrf_with_large_positive(ppr):
    assert ppr.convert_setrf("R5", 34000) == [
        Op("SETLO", ["R5", 208]),
        Op("SETHI", ["R5", 132]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_convert_setrf_with_negative(ppr):
    assert ppr.convert_setrf("R5", -5) == [
        Op("SETLO", ["R5", 251]),
        Op("SETHI", ["R5", 255]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_convert_flags(ppr):
    assert ppr.convert_flags("R8") == [Op("FOFF", [8]), Op("ADD", ["R0", "R8", "R0"])]


def test_convert_halt(ppr):
    assert ppr.convert_halt() == [Op("BRR", [0])]


def test_convert_nop(ppr):
    assert ppr.convert_nop() == [Op("BRR", [1])]


def test_convert_call_with_register(ppr):
    assert ppr.convert_call("R12", REG("R13")) == [Op("CALL", ["R12", "R13"])]


def test_convert_call_with_label(ppr):
    assert ppr.convert_call("R12", Token("SYMBOL", "div")) == [
        Op("SETLO", ["R13", "div"]),
        Op("SETHI", ["R13", "div"]),
        Op("CALL", ["R12", "R13"]),
    ]


def test_convert_neg(ppr):
    assert ppr.convert_neg("R1", "R2") == [
        Op("FON", [8]),
        Op("SUB", ["R1", "R0", "R2"]),
    ]


def test_convert_not(ppr):
    assert ppr.convert_not("R1", "R2") == [
        Op("SETLO", ["R11", 0xFF]),
        Op("SETHI", ["R11", 0xFF]),
        Op("XOR", ["R1", "R11", "R2"]),
    ]


def test_get_labels_with_example(ppr):
    ppr.get_labels(
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
    assert len(ppr.labels) == 4
    assert ppr.labels["data"] == HERA_DATA_START
    assert ppr.labels["data2"] == HERA_DATA_START + 2
    assert ppr.labels["top"] == 0
    assert ppr.labels["bottom"] == 1


def test_get_labels_with_dskip(ppr):
    ppr.get_labels(
        [
            Op("DLABEL", ["data"]),
            Op("INTEGER", [42]),
            Op("DSKIP", [10]),
            Op("DLABEL", ["data2"]),
            Op("INTEGER", [84]),
        ]
    )
    assert len(ppr.labels) == 2
    assert ppr.labels["data"] == HERA_DATA_START
    assert ppr.labels["data2"] == HERA_DATA_START + 11


def test_get_labels_with_lp_string(ppr):
    ppr.get_labels(
        [
            Op("DLABEL", ["S"]),
            Op("LP_STRING", ["hello"]),
            Op("DLABEL", ["X"]),
            Op("INTEGER", [42]),
        ]
    )
    assert len(ppr.labels) == 2
    assert ppr.labels["S"] == HERA_DATA_START
    assert ppr.labels["X"] == HERA_DATA_START + 6


def test_get_labels_with_empty_lp_string(ppr):
    ppr.get_labels(
        [
            Op("DLABEL", ["S"]),
            Op("LP_STRING", [""]),
            Op("DLABEL", ["X"]),
            Op("INTEGER", [42]),
        ]
    )
    assert len(ppr.labels) == 2
    assert ppr.labels["S"] == HERA_DATA_START
    assert ppr.labels["X"] == HERA_DATA_START + 1


def test_preprocess_constant(ppr):
    program = [
        Op("CONSTANT", [Token("SYMBOL", "n"), IntToken(100)]),
        Op(Token("SYMBOL", "SET"), [REG("R1"), Token("SYMBOL", "n")]),
    ]
    assert preprocess(program) == [Op("SETLO", ["R1", 100]), Op("SETHI", ["R1", 0])]


def test_verify_args_with_too_few():
    with pytest.raises(HERAError) as e:
        verify_args("", [REGISTER, REGISTER], [REG("R1")])
    assert "too few" in str(e)


def test_verify_args_with_too_many():
    with pytest.raises(HERAError) as e:
        verify_args("", [REGISTER], [REG("R1"), IntToken(10)])
    assert "too many" in str(e)


def test_verify_args_with_wrong_type():
    with pytest.raises(HERAError) as e1:
        verify_args("", [REGISTER], [IntToken(10)])
    assert "not a register" in str(e1)

    with pytest.raises(HERAError) as e2:
        verify_args("", [U16], [REG("R1")])
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
        verify_args("", [range(-10, 10)], [REG("R1")])
    assert "not an integer" in str(e3)

    r = range(-10, 10)
    verify_args("", [r, r, r], [5, -10, 9])


def test_verify_args_with_constant_symbol():
    verify_args("", [range(0, 100)], [Token("SYMBOL", "n")])


def test_verify_args_with_register_or_label():
    verify_args("", [REGISTER_OR_LABEL], [Token("SYMBOL", "n")])
    verify_args("", [REGISTER_OR_LABEL], [REG("R1")])
