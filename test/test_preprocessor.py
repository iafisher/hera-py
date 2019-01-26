from hera.data import Op, Token
from hera.op import SET, SETHI, SETLO
from hera.preprocessor import preprocess, substitute_label


def R(s):
    return Token("REGISTER", s)


def SYM(s):
    return Token("SYMBOL", s)


def test_substitute_label_with_SETLO():
    labels = {"N": 10}
    assert substitute_label(Op(SYM("SETLO"), [R("R1"), SYM("N")]), labels) == Op(
        "SETLO", ["R1", 10]
    )


def test_substitute_label_with_SETHI():
    labels = {"N": 10}
    assert substitute_label(Op(SYM("SETHI"), [R("R1"), SYM("N")]), labels) == Op(
        "SETHI", ["R1", 10]
    )


def test_substitute_label_with_other_op():
    labels = {"N": 10}
    assert substitute_label(Op(SYM("INC"), [R("R1"), SYM("N")]), labels) == Op(
        "INC", ["R1", 10]
    )


def test_preprocess_constant():
    program = [SET(R("R1"), Token("SYMBOL", "n"))]
    assert preprocess(program, {"n": 100}) == [SETLO("R1", 100), SETHI("R1", 0)]
