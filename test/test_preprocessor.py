import pytest

from lark import Token

from hera.parser import Op
from hera.preprocessor import preprocess, Preprocessor, HERA_DATA_START
from hera.utils import HERAError, IntToken


@pytest.fixture
def ppr():
    return Preprocessor()


def REG(s):
    return Token("REGISTER", s)


def test_preprocess1_set_with_small_positive(ppr):
    assert ppr.preprocess1_set("R5", 18) == [Op("SETLO", ["R5", 18])]


def test_preprocess1_set_with_large_positive(ppr):
    assert ppr.preprocess1_set("R5", 34000) == [
        Op("SETLO", ["R5", 208]),
        Op("SETHI", ["R5", 132]),
    ]


def test_preprocess1_set_with_negative(ppr):
    assert ppr.preprocess1_set("R5", -5) == [
        Op("SETLO", ["R5", 251]),
        Op("SETHI", ["R5", 255]),
    ]


def test_preprocess1_set_with_symbol(ppr):
    assert ppr.preprocess1_set("R5", "whatever") == [
        Op("SETLO", ["R5", "whatever"]),
        Op("SETHI", ["R5", "whatever"]),
    ]


def test_preprocess1_move(ppr):
    assert ppr.preprocess1_move("R5", "R3") == [Op("OR", ["R5", "R3", "R0"])]


def test_preprocess1_con(ppr):
    assert ppr.preprocess1_con() == [Op("FON", [8])]


def test_preprocess1_coff(ppr):
    assert ppr.preprocess1_coff() == [Op("FOFF", [8])]


def test_preprocess1_cbon(ppr):
    assert ppr.preprocess1_cbon() == [Op("FON", [16])]


def test_preprocess1_ccboff(ppr):
    assert ppr.preprocess1_ccboff() == [Op("FOFF", [24])]


def test_preprocess2_label(ppr):
    assert ppr.preprocess2_label("whatever") is None


def test_preprocess2_dlabel(ppr):
    assert ppr.preprocess2_dlabel("whatever") is None


def test_preprocess2_constant(ppr):
    assert ppr.preprocess2_constant("whatever", 5) is None


def test_preprocess1_cmp(ppr):
    assert ppr.preprocess1_cmp("R1", "R2") == [
        Op("FON", [8]),
        Op("SUB", ["R0", "R1", "R2"]),
    ]


def test_preprocess1_setrf_with_small_positive(ppr):
    assert ppr.preprocess1_setrf("R5", 18) == [
        Op("SETLO", ["R5", 18]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_preprocess1_setrf_with_large_positive(ppr):
    assert ppr.preprocess1_setrf("R5", 34000) == [
        Op("SETLO", ["R5", 208]),
        Op("SETHI", ["R5", 132]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_preprocess1_setrf_with_negative(ppr):
    assert ppr.preprocess1_setrf("R5", -5) == [
        Op("SETLO", ["R5", 251]),
        Op("SETHI", ["R5", 255]),
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R5", "R0"]),
    ]


def test_preprocess1_flags(ppr):
    assert ppr.preprocess1_flags("R8") == [
        Op("FOFF", [8]),
        Op("ADD", ["R0", "R8", "R0"]),
    ]


def test_preprocess1_br_with_register(ppr):
    assert ppr.preprocess1_br(REG("R5")) == [Op("BR", ["R5"])]


def test_preprocess1_br_with_label(ppr):
    assert ppr.preprocess1_br(Token("SYMBOL", "top")) == [
        Op("SETLO", ["R11", "top"]),
        Op("SETHI", ["R11", "top"]),
        Op("BR", ["R11"]),
    ]


def test_preprocess1_halt(ppr):
    assert ppr.preprocess1_halt() == [Op("BRR", [0])]


def test_preprocess1_nop(ppr):
    assert ppr.preprocess1_nop() == [Op("BRR", [1])]


def test_preprocess1_call_with_register(ppr):
    assert ppr.preprocess1_call("R12", REG("R13")) == [Op("CALL", ["R12", "R13"])]


def test_preprocess1_call_with_label(ppr):
    assert ppr.preprocess1_call("R12", Token("SYMBOL", "div")) == [
        Op("SETLO", ["R13", "div"]),
        Op("SETHI", ["R13", "div"]),
        Op("CALL", ["R12", "R13"]),
    ]


def test_preprocess1_neg(ppr):
    assert ppr.preprocess1_neg("R1", "R2") == [
        Op("FON", [8]),
        Op("SUB", ["R1", "R0", "R2"]),
    ]


def test_preprocess1_not(ppr):
    assert ppr.preprocess1_not("R1", "R2") == [
        Op("SETLO", ["R11", 0xFF]),
        Op("SETHI", ["R11", 0xFF]),
        Op("XOR", ["R1", "R11", "R2"]),
    ]


def test_resolve_labels_with_example(ppr):
    ppr.resolve_labels(
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


def test_resolve_labels_with_dskip(ppr):
    ppr.resolve_labels(
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


def test_resolve_labels_with_lp_string(ppr):
    ppr.resolve_labels(
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


def test_resolve_labels_with_empty_lp_string(ppr):
    ppr.resolve_labels(
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


def test_assert_args_with_too_few(ppr):
    with pytest.raises(HERAError) as e:
        ppr.assert_args("", [ppr.REGISTER, ppr.REGISTER], [REG("R1")])
    assert "too few" in str(e)


def test_assert_args_with_too_many(ppr):
    with pytest.raises(HERAError) as e:
        ppr.assert_args("", [ppr.REGISTER], [REG("R1"), IntToken(10)])
    assert "too many" in str(e)


def test_assert_args_with_wrong_type(ppr):
    with pytest.raises(HERAError) as e1:
        ppr.assert_args("", [ppr.REGISTER], [IntToken(10)])
    assert "not a register" in str(e1)

    with pytest.raises(HERAError) as e2:
        ppr.assert_args("", [ppr.U16], [REG("R1")])
    assert "not an integer" in str(e2)

    with pytest.raises(HERAError) as e3:
        ppr.assert_args("", [ppr.I8], [REG("R1")])
    assert "not an integer" in str(e3)


def test_assert_args_with_u16_out_of_range(ppr):
    with pytest.raises(HERAError) as e:
        ppr.assert_args("", [ppr.U16], [IntToken(65536)])
    assert "out of range" in str(e)


def test_assert_args_with_negative_u16(ppr):
    with pytest.raises(HERAError) as e:
        ppr.assert_args("", [ppr.U16], [IntToken(-1)])
    assert "must not be negative" in str(e)


def test_assert_args_with_i8_out_of_range(ppr):
    with pytest.raises(HERAError) as e1:
        ppr.assert_args("", [ppr.I8], [IntToken(128)])
    assert "out of range" in str(e1)

    with pytest.raises(HERAError) as e2:
        ppr.assert_args("", [ppr.I8], [IntToken(-129)])
    assert "out of range" in str(e2)


def test_assert_args_with_range_object(ppr):
    with pytest.raises(HERAError) as e1:
        ppr.assert_args("", [range(-10, 10)], [IntToken(-11)])
    assert "out of range" in str(e1)

    with pytest.raises(HERAError) as e2:
        ppr.assert_args("", [range(-10, 10)], [IntToken(10)])
    assert "out of range" in str(e2)

    with pytest.raises(HERAError) as e3:
        ppr.assert_args("", [range(-10, 10)], [REG("R1")])
    assert "not an integer" in str(e3)

    r = range(-10, 10)
    ppr.assert_args("", [r, r, r], [5, -10, 9])


def test_assert_args_with_constant_symbol(ppr):
    ppr.assert_args("", [range(0, 100)], [Token("SYMBOL", "n")])


def test_verify_set_good(ppr):
    ppr.verify_set(REG("R1"), IntToken(-5))


def test_verify_set_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_set(IntToken(10), REG("R1"))
    assert "SET" in str(e)
    assert "not a register" in str(e)


def test_verify_setlo_good(ppr):
    ppr.verify_setlo(REG("R1"), IntToken(-5))


def test_verify_setlo_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_setlo(REG("R1"), REG("R2"))
    assert "SETLO" in str(e)
    assert "not an integer" in str(e)


def test_verify_sethi_good(ppr):
    ppr.verify_sethi(REG("R1"), IntToken(-5))


def test_verify_sethi_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_sethi(REG("R1"), REG("R2"))
    assert "SETHI" in str(e)
    assert "not an integer" in str(e)


def test_verify_and_good(ppr):
    ppr.verify_and(REG("R1"), REG("R2"), REG("R3"))


def test_verify_and_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_and(REG("R1"), REG("R2"))
    assert "AND" in str(e)
    assert "too few args" in str(e)


def test_verify_or_good(ppr):
    ppr.verify_or(REG("R1"), REG("R2"), REG("R3"))


def test_verify_or_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_or(REG("R1"), REG("R2"), REG("R3"), REG("R4"))
    assert "OR" in str(e)
    assert "too many args" in str(e)


def test_verify_add_good(ppr):
    ppr.verify_add(REG("R1"), REG("R2"), REG("R3"))


def test_verify_add_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_add(REG("R1"), REG("R2"), IntToken(17))
    assert "ADD" in str(e)
    assert "not a register" in str(e)


def test_verify_sub_good(ppr):
    ppr.verify_sub(REG("R1"), REG("R2"), REG("R3"))


def test_verify_sub_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_sub(REG("R1"), REG("R2"), IntToken(17))
    assert "SUB" in str(e)
    assert "not a register" in str(e)


def test_verify_mul_good(ppr):
    ppr.verify_mul(REG("R1"), REG("R2"), REG("R3"))


def test_verify_mul_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_mul(REG("R1"), IntToken(17), REG("R2"))
    assert "MUL" in str(e)
    assert "not a register" in str(e)


def test_verify_xor_good(ppr):
    ppr.verify_xor(REG("R1"), REG("R2"), REG("R3"))


def test_verify_xor_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_xor(REG("R1"), IntToken(17), REG("R2"))
    assert "XOR" in str(e)
    assert "not a register" in str(e)


def test_verify_inc_good(ppr):
    ppr.verify_inc(REG("R1"), IntToken(64))


def test_verify_inc_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_inc(REG("R1"), IntToken(65))
    assert "INC" in str(e)
    assert "out of range" in str(e)


def test_verify_dec_good(ppr):
    ppr.verify_dec(REG("R1"), IntToken(64))


def test_verify_dec_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_dec(REG("R1"), IntToken(-1))
    assert "DEC" in str(e)
    assert "out of range" in str(e)


def test_verify_lsl_good(ppr):
    ppr.verify_lsl(REG("R8"), REG("R7"))


def test_verify_lsl_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_lsl(IntToken(10), REG("R6"))
    assert "LSL" in str(e)
    assert "not a register" in str(e)


def test_verify_lsr_good(ppr):
    ppr.verify_lsr(REG("R8"), REG("R7"))


def test_verify_lsr_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_lsr(REG("R6"), IntToken(10))
    assert "LSR" in str(e)
    assert "not a register" in str(e)


def test_verify_lsl8_good(ppr):
    ppr.verify_lsl8(REG("R8"), REG("R7"))


def test_verify_lsl8_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_lsl8(REG("R6"), IntToken(10))
    assert "LSL8" in str(e)
    assert "not a register" in str(e)


def test_verify_lsr8_good(ppr):
    ppr.verify_lsr8(REG("R8"), REG("R7"))


def test_verify_lsr8_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_lsr8(REG("R6"), IntToken(10))
    assert "LSR8" in str(e)
    assert "not a register" in str(e)


def test_verify_asl_good(ppr):
    ppr.verify_asl(REG("R8"), REG("R7"))


def test_verify_asl_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_asl(REG("R6"), IntToken(10))
    assert "ASL" in str(e)
    assert "not a register" in str(e)


def test_verify_asr_good(ppr):
    ppr.verify_asr(REG("R8"), REG("R7"))


def test_verify_asr_bad(ppr):
    with pytest.raises(HERAError) as e:
        ppr.verify_asr(REG("R6"), IntToken(10))
    assert "ASR" in str(e)
    assert "not a register" in str(e)
