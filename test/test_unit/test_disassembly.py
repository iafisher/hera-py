from hera.data import Token
from hera.op import match_bitvector, substitute_bitvector


def test_match_bitvector_with_literal_pattern():
    assert match_bitvector("0101 0101 0101 0101", 0b0101010101010101) == []
    assert match_bitvector("0101 0101 0101 0101", 0) is False


def test_match_bitvector_captures_one_register():
    m = match_bitvector("0000 1111 AAAA 0000", 0b0000111101010000)
    assert m == [Token(Token.REGISTER, 0b0101)]

    m = match_bitvector("0000 1111 AAAA 0000", 0b0000101101010010)
    assert m is False


def test_match_bitvector_captures_one_integer():
    m = match_bitvector("0000 1111 aaaa 0000", 0b0000111101010000)
    assert m == [Token(Token.INT, 0b0101)]


def test_match_bitvector_captures_multiple_args():
    m = match_bitvector("0101 aaaa BBBB cccc", 0b0101011010111111)
    assert m == [
        Token(Token.INT, 0b0110),
        Token(Token.REGISTER, 0b1011),
        Token(Token.INT, 0b1111),
    ]


def test_match_bitvector_captures_args_out_of_order():
    m = match_bitvector("0101 BBBB aaaa cccc", 0b0101011010111111)
    assert m == [
        Token(Token.INT, 0b1011),
        Token(Token.REGISTER, 0b0110),
        Token(Token.INT, 0b1111),
    ]


def test_match_bitvector_captures_split_arg():
    m = match_bitvector("dcba abcd dcba abcd", 0b0111000011100000)

    assert m == [
        Token(Token.INT, 0b1000),
        Token(Token.INT, 0b1010),
        Token(Token.INT, 0b1010),
        Token(Token.INT, 0b0010),
    ]


def test_substitute_bitvector_with_no_args():
    assert substitute_bitvector("0000 1111 0000 1111", []) == bytes([0b1111, 0b1111])


def test_substitute_bitvector_with_one_arg():
    assert substitute_bitvector("0000 aaaa 0000 1111", [7]) == bytes([7, 0b1111])


def test_substitute_bitvector_with_two_args():
    assert substitute_bitvector("0000 aaaa bbbb 1111", [7, 3]) == bytes([7, 63])


def test_substitute_bitvector_with_out_of_order_args():
    bv = substitute_bitvector("bb00 11bb a00a 1aa1", [0b1010, 0b0101])

    assert bv == bytes([0b01001101, 0b10001101])
