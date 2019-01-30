# TODO: The equality checks here don't check type because of the way that Token.__eq__
# is defined.
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


def test_lexer_with_negative_integer():
    lexer = lex_helper("-1")

    assert lexer.tkn == Token(TOKEN.INT, "-1")
    assert lexer.next_token() == Token(TOKEN.EOF, "")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_character_literal():
    lexer = lex_helper("'a'")

    assert lexer.tkn == Token(TOKEN.CHAR, "a")
    assert lexer.next_token() == Token(TOKEN.EOF, "")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_character_literal_backslash_escape():
    lexer = lex_helper("'\\n'")

    assert lexer.tkn == Token(TOKEN.CHAR, "\n")
    assert lexer.next_token() == Token(TOKEN.EOF, "")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_over_long_character_literal():
    lexer = lex_helper("'abc'")

    assert lexer.tkn.type == TOKEN.UNKNOWN


def test_lexer_with_string():
    lexer = lex_helper(
        """\
"a double quote: \\", a backslash: \\\\"
    """
    )

    assert lexer.tkn == Token(TOKEN.STRING, 'a double quote: ", a backslash: \\')
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_empty_string():
    lexer = lex_helper('""')

    assert lexer.tkn == Token(TOKEN.STRING, "")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_include():
    lexer = lex_helper('#include <HERA.h> #include "lib.hera"')

    assert lexer.tkn == Token(TOKEN.INCLUDE, "#include")
    assert lexer.next_token() == Token(TOKEN.BRACKETED, "HERA.h")
    assert lexer.next_token() == Token(TOKEN.INCLUDE, "#include")
    assert lexer.next_token() == Token(TOKEN.STRING, "lib.hera")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_braces():
    lexer = lex_helper("{}")

    assert lexer.tkn == Token(TOKEN.LBRACE, "{")
    assert lexer.next_token() == Token(TOKEN.RBRACE, "}")
    assert lexer.next_token() == Token(TOKEN.EOF, "")


def test_lexer_with_big_example():
    # This isn't a syntactically valid expression, but it doesn't matter to the lexer.
    lexer = lex_helper("@FP_alt R15 0xabc some_symbol :xdc -10; ,, ()+*/?")

    assert lexer.tkn == Token(TOKEN.AT, "@")
    assert lexer.next_token() == Token(TOKEN.REGISTER, "FP_alt")
    assert lexer.next_token() == Token(TOKEN.REGISTER, "R15")
    assert lexer.next_token() == Token(TOKEN.INT, "0xabc")
    assert lexer.next_token() == Token(TOKEN.SYMBOL, "some_symbol")
    assert lexer.next_token() == Token(TOKEN.FMT, "xdc")
    assert lexer.next_token() == Token(TOKEN.INT, "-10")
    assert lexer.next_token() == Token(TOKEN.SEMICOLON, ";")
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
