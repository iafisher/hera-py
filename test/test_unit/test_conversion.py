from hera.checker import convert_ops
from hera.data import Token
from hera.op import ADD, BR, BRR, CALL, FOFF, FON, INTEGER, SET, SETHI, SETLO, SUB
from hera.parser import parse


def helper(argstr):
    oplist, messages = parse(argstr)
    assert not messages.errors
    return oplist[0].convert()


def test_convert_register_branch_with_register():
    ops = helper("BR(R1)")
    assert ops == [BR(Token.R(1))]


def test_convert_register_branch_with_integer():
    # Simulates BR(l) where l = 1000
    ops = helper("BR(1000)")
    assert ops == [
        SETLO(Token.R(11), Token.INT(232)),
        SETHI(Token.R(11), Token.INT(3)),
        BR(Token.R(11)),
    ]


def test_convert_SET():
    ops = helper("SET(R1, 0b100010101010)")
    assert ops == [
        SETLO(Token.R(1), Token.INT(0b10101010)),
        SETHI(Token.R(1), Token.INT(0b1000)),
    ]


def test_convert_CALL():
    # Simulates CALL(R12, l) where l = 1000
    ops = helper("CALL(R12, 1000)")
    assert ops == [
        SETLO(Token.R(13), Token.INT(232)),
        SETHI(Token.R(13), Token.INT(3)),
        CALL(Token.R(12), Token.R(13)),
    ]


def test_convert_CMP():
    ops = helper("CMP(R5, R6)")
    assert ops == [FON(Token.INT(8)), SUB(Token.R(0), Token.R(5), Token.R(6))]


def test_convert_CON():
    ops = helper("CON()")
    assert ops == [FON(Token.INT(8))]


def test_convert_COFF():
    ops = helper("COFF()")
    assert ops == [FOFF(Token.INT(8))]


def test_convert_CBON():
    ops = helper("CBON()")
    assert ops == [FON(Token.INT(0x10))]


def test_convert_CCBOFF():
    ops = helper("CCBOFF()")
    assert ops == [FOFF(Token.INT(0x18))]


def test_convert_FLAGS():
    ops = helper("FLAGS(R14)")
    assert ops == [FOFF(Token.INT(8)), ADD(Token.R(0), Token.R(14), Token.R(0))]


def test_convert_LABEL():
    ops = helper("LABEL(l)")
    assert ops == []


def test_convert_DLABEL():
    ops = helper("DLABEL(l)")
    assert ops == []


def test_convert_NOP():
    ops = helper("NOP()")
    assert ops == [BRR(Token.INT(1))]


def test_convert_HALT():
    ops = helper("HALT()")
    assert ops == [BRR(Token.INT(0))]


def test_convert_non_pseudo_op():
    ops = helper("ADD(R1, R2, R3)")
    assert ops == [ADD(Token.R(1), Token.R(2), Token.R(3))]


def test_convert_ops_with_constant():
    oplist, messages = convert_ops([SET(Token.R(1), Token.SYM("n"))], {"n": 100})

    assert len(messages.errors) == 0
    assert oplist == [
        SETLO(Token.R(1), Token.INT(100)),
        SETHI(Token.R(1), Token.INT(0)),
    ]


def test_convert_ops_reports_error_for_invalid_relative_branch():
    oplist, messages = convert_ops([BRR(Token.SYM("l"))], {"l": 9000})

    assert len(messages.errors) == 1
    assert "too far" in messages.errors[0][0]


def test_convert_ops_does_not_report_error_for_valid_relative_branch():
    data = [INTEGER(Token.INT(1))] * 200
    oplist, messages = convert_ops(data + [BRR(Token.SYM("l"))], {"l": 1})

    assert len(messages.errors) == 0
    assert oplist == data + [BRR(Token.INT(1))]
