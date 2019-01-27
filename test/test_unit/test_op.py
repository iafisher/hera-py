from hera.data import Token
from hera.op import SET


def test_op_to_string():
    assert str(SET(Token("REGISTER", "R1"), Token("SYMBOL", "top"))) == "SET(R1, top)"


def test_op_to_string_with_integer():
    assert str(SET(Token("REGISTER", "R1"), Token("INTEGER", 12))) == "SET(R1, 12)"
