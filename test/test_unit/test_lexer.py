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


def test_lex_mini_language_with_symbols_starting_with_M():
    lexer = lex_helper("more m")

    assert lexer.tkn == Token(TOKEN.SYMBOL, "more")
    assert lexer.next_token() == Token(TOKEN.SYMBOL, "m")
    assert lexer.next_token() == Token(TOKEN.EOF, "")
    assert lexer.next_token() == Token(TOKEN.EOF, "")
