import pytest

from hera.parser import Op, parse


def test_parse_op():
    assert parse('SETLO(R1, 4)') == [Op('SETLO', ['R1', 4])]


def test_parse_op_with_label():
    parsed = parse('SETLO(R1, top)')
    assert parsed == [Op('SETLO', ['R1', 'top'])]
    assert parsed[0].args[0].type == 'REGISTER'
    assert parsed[0].args[1].type == 'SYMBOL'


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
