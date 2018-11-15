import pytest

from hera.parser import Op, parse, replace_escapes
from hera.utils import HERAError


def test_replace_escapes_with_one_escape():
    assert replace_escapes('abc\\ndef') == 'abc\ndef'


def test_replace_escapes_with_many_escapes():
    assert replace_escapes('\\\\\\n\\ta\\"') == '\\\n\ta"'


def test_replace_escapes_with_invalid_escape():
    assert replace_escapes('\\c') == '\\c'


def test_parse_op():
    assert parse('SETLO(R1, 4)') == [Op('SETLO', ['R1', 4])]


def test_parse_op_with_label():
    parsed = parse('SETLO(R1, top)')
    assert parsed == [Op('SETLO', ['R1', 'top'])]
    assert parsed[0].args[0].type == 'REGISTER'
    assert parsed[0].args[1].type == 'SYMBOL'


def test_parse_string():
    parsed = parse('LP_STRING("hello")')
    assert parsed == [Op('LP_STRING', ['hello'])]
    assert parsed[0].args[0].type == 'STRING'


def test_parse_empty_string():
    assert parse('LP_STRING("")') == [Op('LP_STRING', [''])]


def test_parse_string_with_escapes():
    assert parse('LP_STRING("multiline\\nstring with quotes: \\"\\"")') == [
        Op('LP_STRING', ['multiline\nstring with quotes: ""']),
    ]


def test_parse_signed_number():
    assert parse('SETLO(R1, -12)') == [Op('SETLO', ['R1', -12])]


def test_parse_hex_number():
    assert parse('SETLO(R4, 0x5f)') == [Op('SETLO', ['R4', 0x5f])]


def test_parse_negative_hex_number():
    assert parse('SETLO(R7, -0x2B)') == [Op('SETLO', ['R7', -0x2b])]


def test_parse_binary_number():
    assert parse('SETLO(R5, 0b10110)') == [Op('SETLO', ['R5', 22])]


def test_parse_negative_binary_number():
    assert parse('SETLO(R5, -0b10110)') == [Op('SETLO', ['R5', -22])]


def test_parse_octal_number():
    assert parse('SETLO(R3, 0o173)') == [Op('SETLO', ['R3', 123])]


def test_parse_negative_octal_number():
    assert parse('SETLO(R3, -0o173)') == [Op('SETLO', ['R3', -123])]


def test_parse_single_line_comment():
    assert parse('SETLO(R1, 0)  // R1 <- 0') == [Op('SETLO', ['R1', 0])]


def test_parse_another_single_line_comments():
    program = '''\
// Single-line comment
SETLO(R9, 42)
    '''
    assert parse(program) == [Op('SETLO', ['R9', 42])]


def test_parse_multiline_comment():
    program = '''\
/* Starts on this line
   ends on this one */
SETLO(R1, 1)
    '''
    assert parse(program) == [Op('SETLO', ['R1', 1])]


def test_parse_missing_comma():
    with pytest.raises(HERAError):
        parse('ADD(R1, R2 R3)')


def test_parse_missing_parenthesis():
    with pytest.raises(HERAError):
        parse('LSL8(R1, R1')


def test_parse_missing_end_quote():
    with pytest.raises(HERAError):
        parse('LP_STRING("forgot to close my string)')
