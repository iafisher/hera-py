from hera.data import Token
from hera.lexer import Lexer, TOKEN


def lex_helper(text):
    return Lexer(text)


def test_lexer_with_register():
    lexer = lex_helper("r1")

    assert lexer.tkn == Token(TOKEN.REGISTER, "r1")
    assert lexer.next_token() == Token(TOKEN.EOF, "")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_integer():
    lexer = lex_helper("0")

    assert lexer.tkn == Token(TOKEN.INT, "0")
    assert lexer.next_token() == Token(TOKEN.EOF, "")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_big_example():
    # This isn't a syntactically valid expression, but it doesn't matter to the lexer.
    lexer = lex_helper("@FP_alt R15 0xabc some_symbol :xdc -10 ,, ()+*/?")

    assert lexer.tkn == Token(TOKEN.AT, "@")
    assert lexer.next_token() == Token(TOKEN.REGISTER, "FP_alt")
    assert lexer.next_token() == Token(TOKEN.REGISTER, "R15")
    assert lexer.next_token() == Token(TOKEN.INT, "0xabc")
    assert lexer.next_token() == Token(TOKEN.SYMBOL, "some_symbol")
    assert lexer.next_token() == Token(TOKEN.FMT, "xdc")
    assert lexer.next_token() == Token(TOKEN.MINUS, "-")
    assert lexer.next_token() == Token(TOKEN.INT, "10")
    assert lexer.next_token() == Token(TOKEN.COMMA, ",")
    assert lexer.next_token() == Token(TOKEN.COMMA, ",")
    assert lexer.next_token() == Token(TOKEN.LPAREN, "(")
    assert lexer.next_token() == Token(TOKEN.RPAREN, ")")
    assert lexer.next_token() == Token(TOKEN.PLUS, "+")
    assert lexer.next_token() == Token(TOKEN.ASTERISK, "*")
    assert lexer.next_token() == Token(TOKEN.SLASH, "/")
    assert lexer.next_token() == Token(TOKEN.UNKNOWN, "?")
    assert lexer.next_token() == Token(TOKEN.EOF, "")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_symbols_starting_with_M():
    lexer = lex_helper("more m")

    assert lexer.tkn == Token(TOKEN.SYMBOL, "more")
    assert lexer.next_token() == Token(TOKEN.SYMBOL, "m")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_single_line_comment():
    lexer = lex_helper("1 // a comment\n 2")

    assert lexer.tkn == Token(TOKEN.INT, "1")
    assert lexer.next_token() == Token(TOKEN.INT, "2")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_empty_single_line_comment():
    lexer = lex_helper("//")

    assert lexer.tkn == Token(TOKEN.EOF, "")


def test_lexer_with_multiple_single_line_comments():
    lexer = lex_helper(
        """\
1 // one
2 // two
// no three
4 // four"""
    )

    assert lexer.tkn == Token(TOKEN.INT, "1")
    assert lexer.next_token() == Token(TOKEN.INT, "2")
    assert lexer.next_token() == Token(TOKEN.INT, "4")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_multiline_comment():
    lexer = lex_helper(
        """\
1 /*
a multiline comment
*/ 2"""
    )

    assert lexer.tkn == Token(TOKEN.INT, "1")
    assert lexer.next_token() == Token(TOKEN.INT, "2")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_multiline_comment_abutting_value():
    lexer = lex_helper("1/*\n\n*/2")

    assert lexer.tkn == Token(TOKEN.INT, "1")
    assert lexer.next_token() == Token(TOKEN.INT, "2")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_tricky_multiline_comment():
    lexer = lex_helper("/*/*** 123/ */")

    assert lexer.tkn == Token(TOKEN.EOF, "")
