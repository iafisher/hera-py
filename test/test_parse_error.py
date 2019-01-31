import pytest

from .utils import execute_program_helper


def test_parse_unclosed_string_literal(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper('LP_STRING("hello)')

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: unclosed string literal, line 1 col 11 of <stdin>

  LP_STRING("hello)
            ^

"""
    )


def test_parse_unclosed_string_literal_ending_with_backslash(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper('LP_STRING("devilish\\')

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: unclosed string literal, line 1 col 11 of <stdin>

  LP_STRING("devilish\\
            ^

"""
    )


def test_parse_unclosed_angle_include(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("#include <data.h")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: unclosed bracketed expression, line 1 col 11 of <stdin>

  #include <data.h
            ^

"""
    )
