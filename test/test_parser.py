import pytest

from hera.parser import Op, parse


def test_parse_op():
    assert parse('SETLO(R1, 4)') == [Op('SETLO', [1, 4])]


def test_parse_signed_number():
    assert parse('SETLO(R1, -12)') == [Op('SETLO', [1, -12])]


def test_parse_hex_number():
    assert parse('SETLO(R4, 0x5f)') == [Op('SETLO', [4, 0x5f])]


def test_parse_negative_hex_number():
    assert parse('SETLO(R7, -0x2B)') == [Op('SETLO', [7, -0x2b])]


def test_parse_binary_number():
    assert parse('SETLO(R5, 0b10110)') == [Op('SETLO', [5, 22])]


def test_parse_negative_binary_number():
    assert parse('SETLO(R5, -0b10110)') == [Op('SETLO', [5, -22])]


def test_parse_multiline_comment():
    program = '''\
/* Starts on this line
   ends on this one */
SETLO(R1, 1)
'''
    assert parse(program) == [Op('SETLO', [1, 1])]
