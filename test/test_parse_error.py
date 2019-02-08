import pytest

from .utils import execute_program_helper


def test_parse_error_for_unclosed_string_literal(capsys):
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


def test_parse_error_for_unclosed_string_literal_ending_with_backslash(capsys):
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


def test_parse_error_for_unclosed_angle_include(capsys):
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


def test_parse_error_for_cpp_boilerplate_missing_left_parenthesis(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("void HERA_main) { }")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected left parenthesis, line 1 col 15 of <stdin>

  void HERA_main) { }
                ^

"""
    )


def test_parse_error_for_cpp_boilerplate_missing_right_parenthesis(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("void HERA_main( { }")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected right parenthesis, line 1 col 17 of <stdin>

  void HERA_main( { }
                  ^

"""
    )


def test_parse_error_for_cpp_boilerplate_missing_left_curly_brace(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("void HERA_main()  }")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected left curly brace, line 1 col 19 of <stdin>

  void HERA_main()  }
                    ^

"""
    )


def test_parse_error_for_error_in_cpp_boilerplate(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("void HERA_main) { SET(R1 1) }")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected left parenthesis, line 1 col 15 of <stdin>

  void HERA_main) { SET(R1 1) }
                ^

Error: expected comma or right parenthesis, line 1 col 26 of <stdin>

  void HERA_main) { SET(R1 1) }
                           ^

"""
    )


def test_parse_error_for_two_symbols_in_a_row(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET LO(R1, 1)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected left parenthesis, line 1 col 5 of <stdin>

  SET LO(R1, 1)
      ^

Error: unknown instruction `LO`, line 1 col 5 of <stdin>

  SET LO(R1, 1)
      ^

"""
    )


def test_parse_error_for_unclosed_arglist(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(R1, 4\n")

    captured = capsys.readouterr().err
    assert (
        captured
        == "\nError: expected comma or right parenthesis, line 2 col 1 of <stdin>\n"
    )


def test_parse_error_for_trailing_comma_in_arglist(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(R1, 4,)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected value, line 1 col 11 of <stdin>

  SET(R1, 4,)
            ^

"""
    )


def test_parse_error_for_arglist_is_just_a_comma(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(,)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected value, line 1 col 5 of <stdin>

  SET(,)
      ^

Error: expected value, line 1 col 6 of <stdin>

  SET(,)
       ^

"""
    )


def test_parse_error_for_include_following_by_invalid_token(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("#include HERA")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected quote or angle-bracket delimited string, line 1 col 10 of <stdin>

  #include HERA
           ^

"""
    )


def test_parse_error_for_arithmetic_expression(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(R1, 4*4)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected comma or right parenthesis, line 1 col 10 of <stdin>

  SET(R1, 4*4)
           ^

"""
    )


def test_parse_error_for_invalid_integer_literal(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(R1, 0xg)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: invalid integer literal, line 1 col 9 of <stdin>

  SET(R1, 0xg)
          ^

"""
    )


def test_parse_error_for_non_ASCII_byte(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper('LP_STRING("привет")')

    captured = capsys.readouterr().err
    assert captured == "\nError: non-ASCII byte in file.\n"


def test_parse_error_for_non_ASCII_byte_in_file(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper('#include "test/assets/error/non_ascii_byte.hera"')

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: non-ASCII byte in file, line 1 col 10 of <stdin>

  #include "test/assets/error/non_ascii_byte.hera"
           ^

"""
    )


def test_parse_error_for_over_long_character_literal(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(R1, 'abc')")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: over-long character literal, line 1 col 9 of <stdin>

  SET(R1, 'abc')
          ^

"""
    )
