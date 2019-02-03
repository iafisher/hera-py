from hera.checker import convert_ops
from hera.data import RegisterToken, Token, TOKEN
from hera.op import (
    ADD,
    BR,
    BRR,
    CALL,
    FOFF,
    FON,
    INTEGER,
    resolve_ops,
    SET,
    SETHI,
    SETLO,
    SUB,
)
from hera.parser import parse


def helper(argstr):
    oplist, messages = parse(argstr)
    assert not messages.errors
    oplist, messages = resolve_ops(oplist)
    assert not messages.errors
    return oplist[0].convert()


def SYM(s):
    return Token(TOKEN.SYMBOL, s)


def test_convert_register_branch_with_register():
    ops = helper("BR(R1)")
    assert ops == [BR(1)]


def test_convert_register_branch_with_integer():
    # Simulates BR(l) where l = 1000
    ops = helper("BR(1000)")
    assert ops == [SETLO(11, 232), SETHI(11, 3), BR(11)]


def test_convert_SET():
    ops = helper("SET(R1, 0b100010101010)")
    assert ops == [SETLO(1, 0b10101010), SETHI(1, 0b1000)]


def test_convert_CALL():
    # Simulates CALL(R12, l) where l = 1000
    ops = helper("CALL(R12, 1000)")
    assert ops == [SETLO(13, 232), SETHI(13, 3), CALL(12, 13)]


def test_convert_CMP():
    ops = helper("CMP(R5, R6)")
    assert ops == [FON(8), SUB(0, 5, 6)]


def test_convert_CON():
    ops = helper("CON()")
    assert ops == [FON(8)]


def test_convert_COFF():
    ops = helper("COFF()")
    assert ops == [FOFF(8)]


def test_convert_CBON():
    ops = helper("CBON()")
    assert ops == [FON(0x10)]


def test_convert_CCBOFF():
    ops = helper("CCBOFF()")
    assert ops == [FOFF(0x18)]


def test_convert_FLAGS():
    ops = helper("FLAGS(R14)")
    assert ops == [FOFF(8), ADD(0, 14, 0)]


def test_convert_LABEL():
    ops = helper("LABEL(l)")
    assert ops == []


def test_convert_DLABEL():
    ops = helper("DLABEL(l)")
    assert ops == []


def test_convert_NOP():
    ops = helper("NOP()")
    assert ops == [BRR(1)]


def test_convert_HALT():
    ops = helper("HALT()")
    assert ops == [BRR(0)]


def test_convert_non_pseudo_op():
    ops = helper("ADD(R1, R2, R3)")
    assert ops == [ADD(1, 2, 3)]


def test_convert_ops_with_constant():
    oplist, messages = convert_ops([SET(RegisterToken("R1"), SYM("n"))], {"n": 100})

    assert len(messages.errors) == 0
    assert oplist == [SETLO(1, 100), SETHI(1, 0)]


def test_convert_ops_reports_error_for_invalid_relative_branch():
    oplist, messages = convert_ops([BRR(SYM("l"))], {"l": 9000})

    assert len(messages.errors) == 1
    assert "too far" in messages.errors[0][0]


def test_convert_ops_does_not_report_error_for_valid_relative_branch():
    data = [INTEGER(1)] * 200
    oplist, messages = convert_ops(data + [BRR(SYM("l"))], {"l": 1})

    assert len(messages.errors) == 0
    assert oplist == data + [BRR(1)]
