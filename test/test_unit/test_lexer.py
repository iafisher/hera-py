from hera.data import Token
from hera.lexer import Lexer


def lex_helper(text):
    return Lexer(text)


def eq(tkn1, tkn2):
    return tkn1 == tkn2 and tkn1.type == tkn2.type


def test_lexer_with_register():
    lexer = lex_helper("r1")

    assert eq(lexer.tkn, Token(Token.REGISTER, "r1"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_integer():
    lexer = lex_helper("0")

    assert eq(lexer.tkn, Token(Token.INT, "0"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_negative_integer():
    lexer = lex_helper("-1")

    assert eq(lexer.tkn, Token(Token.INT, "-1"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_negative_hex_number():
    lexer = lex_helper("-0xabc")

    assert eq(lexer.tkn, Token(Token.INT, "-0xabc"))


def test_lexer_with_invalid_hex_number():
    lexer = lex_helper("0xghi")

    assert eq(lexer.tkn, Token(Token.INT, "0xghi"))


def test_lexer_with_invalid_octal_number():
    lexer = lex_helper("0o999")

    assert eq(lexer.tkn, Token(Token.INT, "0o999"))


def test_lexer_with_character_literal():
    lexer = lex_helper("'a'")

    assert eq(lexer.tkn, Token(Token.CHAR, "a"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_consecutive_character_literals():
    lexer = lex_helper("'a''b'")

    assert eq(lexer.tkn, Token(Token.CHAR, "a"))
    assert eq(lexer.next_token(), Token(Token.CHAR, "b"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_character_literal_backslash_escape():
    lexer = lex_helper("'\\n'")

    assert eq(lexer.tkn, Token(Token.CHAR, "\n"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_hex_escapes():
    lexer = lex_helper("'\\x41' \"\\x41\"")

    assert eq(lexer.tkn, Token(Token.CHAR, "A"))
    assert eq(lexer.next_token(), Token(Token.STRING, "A"))


def test_lexer_with_octal_escapes():
    lexer = lex_helper("'\\0''\\12' \"\\141\"")

    assert eq(lexer.tkn, Token(Token.CHAR, "\x00"))
    assert eq(lexer.next_token(), Token(Token.CHAR, "\n"))
    assert eq(lexer.next_token(), Token(Token.STRING, "a"))


def test_lexer_with_invalid_hex_escape():
    lexer = lex_helper("'\\xa'  \"\\xgh\"")

    assert len(lexer.messages.warnings) == 1
    assert eq(lexer.tkn, Token(Token.ERROR, "over-long character literal"))
    assert eq(lexer.next_token(), Token(Token.STRING, "xgh"))
    assert len(lexer.messages.warnings) == 2


def test_lexer_with_over_long_character_literal():
    lexer = lex_helper("'abc' 10")

    assert eq(lexer.tkn, Token(Token.ERROR, "over-long character literal"))
    assert eq(lexer.next_token(), Token(Token.INT, "10"))


def test_lexer_with_string():
    lexer = lex_helper(
        """\
"a double quote: \\", a backslash: \\\\"
    """
    )

    assert eq(lexer.tkn, Token(Token.STRING, 'a double quote: ", a backslash: \\'))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_empty_string():
    lexer = lex_helper('""')

    assert eq(lexer.tkn, Token(Token.STRING, ""))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_unclosed_string_literal():
    lexer = lex_helper('"hello')

    assert eq(lexer.tkn, Token(Token.ERROR, "unclosed string literal"))


def test_lexer_with_unclosed_character_literal():
    lexer = lex_helper("'a")

    assert eq(lexer.tkn, Token(Token.ERROR, "unclosed character literal"))


def test_lexer_with_unclosed_bracketed_expression():
    lexer = lex_helper("<abc")

    assert eq(lexer.tkn, Token(Token.ERROR, "unclosed bracketed expression"))


def test_lexer_with_include():
    lexer = lex_helper('#include <HERA.h> #include "lib.hera"')

    assert eq(lexer.tkn, Token(Token.INCLUDE, "#include"))
    assert eq(lexer.next_token(), Token(Token.BRACKETED, "HERA.h"))
    assert eq(lexer.next_token(), Token(Token.INCLUDE, "#include"))
    assert eq(lexer.next_token(), Token(Token.STRING, "lib.hera"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_braces():
    lexer = lex_helper("{}")

    assert eq(lexer.tkn, Token(Token.LBRACE, "{"))
    assert eq(lexer.next_token(), Token(Token.RBRACE, "}"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_big_example():
    # This isn't a syntactically valid expression, but it doesn't matter to the lexer.
    lexer = lex_helper("@FP_alt R15 0xabc some_symbol :xdc -10; ,, ()+*/?")

    assert eq(lexer.tkn, Token(Token.AT, "@"))
    assert eq(lexer.next_token(), Token(Token.REGISTER, "FP_alt"))
    assert eq(lexer.next_token(), Token(Token.REGISTER, "R15"))
    assert eq(lexer.next_token(), Token(Token.INT, "0xabc"))
    assert eq(lexer.next_token(), Token(Token.SYMBOL, "some_symbol"))
    assert eq(lexer.next_token(), Token(Token.FMT, "xdc"))
    assert eq(lexer.next_token(), Token(Token.INT, "-10"))
    assert eq(lexer.next_token(), Token(Token.SEMICOLON, ";"))
    assert eq(lexer.next_token(), Token(Token.COMMA, ","))
    assert eq(lexer.next_token(), Token(Token.COMMA, ","))
    assert eq(lexer.next_token(), Token(Token.LPAREN, "("))
    assert eq(lexer.next_token(), Token(Token.RPAREN, ")"))
    assert eq(lexer.next_token(), Token(Token.PLUS, "+"))
    assert eq(lexer.next_token(), Token(Token.ASTERISK, "*"))
    assert eq(lexer.next_token(), Token(Token.SLASH, "/"))
    assert eq(lexer.next_token(), Token(Token.UNKNOWN, "?"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_symbols_starting_with_M():
    lexer = lex_helper("more m")

    assert eq(lexer.tkn, Token(Token.SYMBOL, "more"))
    assert eq(lexer.next_token(), Token(Token.SYMBOL, "m"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_single_line_comment():
    lexer = lex_helper("1 // a comment\n 2")

    assert eq(lexer.tkn, Token(Token.INT, "1"))
    assert eq(lexer.next_token(), Token(Token.INT, "2"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_empty_single_line_comment():
    lexer = lex_helper("//")

    assert eq(lexer.tkn, Token(Token.EOF, ""))


def test_lexer_with_multiple_single_line_comments():
    lexer = lex_helper(
        """\
1 // one
2 // two
// no three
4 // four"""
    )

    assert eq(lexer.tkn, Token(Token.INT, "1"))
    assert eq(lexer.next_token(), Token(Token.INT, "2"))
    assert eq(lexer.next_token(), Token(Token.INT, "4"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_multiline_comment():
    lexer = lex_helper(
        """\
1 /*
a multiline comment
*/ 2"""
    )

    assert eq(lexer.tkn, Token(Token.INT, "1"))
    assert eq(lexer.next_token(), Token(Token.INT, "2"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_multiline_comment_abutting_value():
    lexer = lex_helper("1/*\n\n*/2")

    assert eq(lexer.tkn, Token(Token.INT, "1"))
    assert eq(lexer.next_token(), Token(Token.INT, "2"))
    assert eq(lexer.next_token(), Token(Token.EOF, ""))


def test_lexer_with_tricky_multiline_comment():
    lexer = lex_helper("/*/*** 123/ */")

    assert eq(lexer.tkn, Token(Token.EOF, ""))
