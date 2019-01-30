from hera.lexer import MiniLexer, Token


def lex_helper(text):
    return MiniLexer(text)


def test_lex_mini_language_with_small_example():
    lexer = lex_helper("r1")

    assert lexer.next_token() == (Token.REGISTER, "r1")
    assert lexer.next_token() == (Token.EOF, "")
    assert lexer.next_token() == (Token.EOF, "")


def test_lex_mini_language_with_big_example():
    # This isn't a syntactically valid expression, but it doesn't matter to the lexer.
    lexer = lex_helper("@FP_alt R15 0xabc some_symbol :xdc -10 ,, ()+*/?")

    assert lexer.next_token() == (Token.AT, "@")
    assert lexer.next_token() == (Token.REGISTER, "FP_alt")
    assert lexer.next_token() == (Token.REGISTER, "R15")
    assert lexer.next_token() == (Token.INT, "0xabc")
    assert lexer.next_token() == (Token.SYMBOL, "some_symbol")
    assert lexer.next_token() == (Token.FMT, "xdc")
    assert lexer.next_token() == (Token.MINUS, "-")
    assert lexer.next_token() == (Token.INT, "10")
    assert lexer.next_token() == (Token.COMMA, ",")
    assert lexer.next_token() == (Token.COMMA, ",")
    assert lexer.next_token() == (Token.LPAREN, "(")
    assert lexer.next_token() == (Token.RPAREN, ")")
    assert lexer.next_token() == (Token.PLUS, "+")
    assert lexer.next_token() == (Token.ASTERISK, "*")
    assert lexer.next_token() == (Token.SLASH, "/")
    assert lexer.next_token() == (Token.UNKNOWN, "?")
    assert lexer.next_token() == (Token.EOF, "")
    assert lexer.next_token() == (Token.EOF, "")


def test_lex_mini_language_with_symbols_starting_with_M():
    lexer = lex_helper("more m")

    assert lexer.next_token() == (Token.SYMBOL, "more")
    assert lexer.next_token() == (Token.SYMBOL, "m")
    assert lexer.next_token() == (Token.EOF, "")
    assert lexer.next_token() == (Token.EOF, "")
