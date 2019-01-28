from hera.op import ADD, BR, BRR, CALL, FOFF, FON, resolve_ops, SETHI, SETLO, SUB
from hera.parser import parse


def helper(argstr):
    oplist, messages = parse(argstr)
    assert not messages.errors
    oplist, messages = resolve_ops(oplist)
    assert not messages.errors
    return oplist[0].convert()


def test_convert_register_branch_with_register():
    ops = helper("BR(R1)")
    assert ops == [BR("R1")]


def test_convert_register_branch_with_integer():
    # Simulates BR(l) where l = 1000
    ops = helper("BR(1000)")
    assert ops == [SETLO("R11", 232), SETHI("R11", 3), BR("R11")]


def test_convert_SET():
    ops = helper("SET(R1, 0b100010101010)")
    assert ops == [SETLO("R1", 0b10101010), SETHI("R1", 0b1000)]


def test_convert_CALL():
    # Simulates CALL(R12, l) where l = 1000
    ops = helper("CALL(R12, 1000)")
    assert ops == [SETLO("R13", 232), SETHI("R13", 3), CALL("R12", "R13")]


def test_convert_CMP():
    ops = helper("CMP(R5, R6)")
    assert ops == [FON(8), SUB("R0", "R5", "R6")]


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
    assert ops == [FOFF(8), ADD("R0", "R14", "R0")]


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
    assert ops == [ADD("R1", "R2", "R3")]
