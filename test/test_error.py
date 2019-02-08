import pytest

from hera.main import main
from .utils import execute_program_helper


def test_error_message_for_missing_comma(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SETLO(R1 40)")

    captured = capsys.readouterr()
    assert "SETLO(R1 40)" in captured.err
    assert "line 1" in captured.err
    assert "col 10" in captured.err


def test_error_message_for_invalid_register(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(R17, 65)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: R17 is not a valid register, line 1 col 5 of <stdin>

  SET(R17, 65)
      ^

"""
    )


def test_error_message_for_invalid_register_with_weird_syntax(capsys):
    program = """\
SET(
\tR17,
\t65)
"""
    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: R17 is not a valid register, line 2 col 2 of <stdin>

  \tR17,
  \t^

"""
    )


def test_multiple_error_messages(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("ADD(R1, 10)\nINC(R4)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: too few args to ADD (expected 3), line 1 col 1 of <stdin>

  ADD(R1, 10)
  ^

Error: expected register, line 1 col 9 of <stdin>

  ADD(R1, 10)
          ^

Error: too few args to INC (expected 2), line 2 col 1 of <stdin>

  INC(R4)
  ^

"""
    )


def test_error_message_from_include(capsys):
    with pytest.raises(SystemExit):
        main(["test/assets/error/from_include.hera"])

    captured = capsys.readouterr()
    assert "SET(R1, R2)  // error!" in captured.err
    assert "ADD(R1, R2)  // error!" in captured.err
    assert "test/assets/error/from_include.hera" in captured.err
    assert "test/assets/error/included.hera" in captured.err


def test_dskip_overflow_program(capsys):
    program = """\
DSKIP(0xFFFF)
DLABEL(N)
INTEGER(42)

SET(R1, N)
    """
    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: past the end of available memory, line 1 col 1 of <stdin>

  DSKIP(0xFFFF)
  ^

"""
    )


def test_error_for_use_of_constant_before_declaration(capsys):
    program = "DSKIP(N)\nCONSTANT(N, 100)"

    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: undefined constant, line 1 col 7 of <stdin>

  DSKIP(N)
        ^

"""
    )


def test_error_for_dskip_with_register(capsys):
    program = "DSKIP(R1)"

    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: expected integer, line 1 col 7 of <stdin>

  DSKIP(R1)
        ^

"""
    )


def test_error_for_use_of_constant_before_include(capsys):
    program = 'SET(R1, N)\n#include "test/assets/error/constant_decl.hera"'

    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: undefined constant, line 1 col 9 of <stdin>

  SET(R1, N)
          ^

Error: data statement after code, line 1 col 1 of test/assets/error/constant_decl.hera

  CONSTANT(N, 100)
  ^

"""
    )


def test_error_for_recursive_constant_declaration(capsys):
    program = "CONSTANT(N, N)"

    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: undefined constant, line 1 col 13 of <stdin>

  CONSTANT(N, N)
              ^

"""
    )


def test_constant_redefinition_error(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("CONSTANT(N, 1)\nCONSTANT(N, 2)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: symbol `N` has already been defined, line 2 col 1 of <stdin>

  CONSTANT(N, 2)
  ^

"""
    )


def test_data_after_code(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(R1, 1)\nINTEGER(42)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: data statement after code, line 2 col 1 of <stdin>

  INTEGER(42)
  ^

"""
    )


def test_error_message_after_symbol_table_error(capsys):
    # Make sure that an error generating the symbol table doesn't immediately end the
    # program--other type errors should still be caught.
    with pytest.raises(SystemExit):
        execute_program_helper("DSKIP(N)\nADD(R1, R2)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: undefined constant, line 1 col 7 of <stdin>

  DSKIP(N)
        ^

Error: too few args to ADD (expected 3), line 2 col 1 of <stdin>

  ADD(R1, R2)
  ^

"""
    )


def test_overflowing_CONSTANT(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("CONSTANT(N, 0xFFFFF)\nSET(R1, N)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: integer must be in range [-32768, 65536), line 1 col 13 of <stdin>

  CONSTANT(N, 0xFFFFF)
              ^

"""
    )


def test_overflowing_integer_literal(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(R1, 0xFFFFF)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: integer must be in range [-32768, 65536), line 1 col 9 of <stdin>

  SET(R1, 0xFFFFF)
          ^

"""
    )


def test_relative_branching_too_far(capsys):
    program = "BRR(l)\n" + ("SET(R1, 1)\n" * 100) + "LABEL(l)"
    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: label is too far for a relative branch, line 1 col 5 of <stdin>

  BRR(l)
      ^

"""
    )


def test_nonexistent_include(capsys):
    program = '#include "unicorn"'
    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: file "unicorn" does not exist, line 1 col 10 of <stdin>

  #include "unicorn"
           ^

"""
    )


def test_invalid_octal_number(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SET(R1, 018)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Warning: consider using "0o" prefix for octal numbers, line 1 col 9 of <stdin>

  SET(R1, 018)
          ^

Error: invalid integer literal, line 1 col 9 of <stdin>

  SET(R1, 018)
          ^

"""
    )


def test_include_before_data(capsys):
    program = """\
#include "test/assets/error/included_before_data.hera"

DLABEL(X)
INTEGER(42)

SET(R1, X)
LOAD(R2, 0, R1)
"""
    with pytest.raises(SystemExit):
        execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: data statement after code, line 3 col 1 of <stdin>

  DLABEL(X)
  ^

Error: data statement after code, line 4 col 1 of <stdin>

  INTEGER(42)
  ^

"""
    )


def test_error_for_interrupt_instructions(capsys):
    with pytest.raises(SystemExit):
        execute_program_helper("SWI(10)\nRTI()")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Error: hera-py does not support SWI, line 1 col 1 of <stdin>

  SWI(10)
  ^

Error: hera-py does not support RTI, line 2 col 1 of <stdin>

  RTI()
  ^

"""
    )


def test_mega_error(capsys):
    with pytest.raises(SystemExit):
        main(["test/assets/error/mega_error.hera"])

    captured = capsys.readouterr().err
    assert (
        captured
        == """\
Warning: consider using "0o" prefix for octal numbers, line 11 col 9 of test/assets/error/mega_error.hera

  SET(R2, 01)
          ^

Warning: unrecognized backslash escape, line 17 col 13 of test/assets/error/mega_error.hera

  LP_STRING("\\y")
              ^

Error: expected comma or right parenthesis, line 2 col 8 of test/assets/error/mega_error.hera

  SET(R1 40)
         ^

Error: over-long character literal, line 14 col 11 of test/assets/error/mega_error.hera

  SETLO(R7, 'ab')
            ^

Error: unclosed string literal, line 20 col 9 of test/assets/error/mega_error.hera

  SET(R1, "
          ^

Error: expected integer, line 5 col 6 of test/assets/error/mega_error.hera

  FOFF(R1)
       ^

Error: too few args to ADD (expected 3), line 8 col 1 of test/assets/error/mega_error.hera

  ADD('c', "abc")
  ^

Error: expected register, line 8 col 6 of test/assets/error/mega_error.hera

  ADD('c', "abc")
       ^

Error: expected register, line 8 col 10 of test/assets/error/mega_error.hera

  ADD('c', "abc")
           ^

Error: data statement after code, line 17 col 1 of test/assets/error/mega_error.hera

  LP_STRING("\\y")
  ^

"""
    )
