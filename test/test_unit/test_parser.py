from hera.data import Token
from hera.op import ADD, INC, LABEL, RTI, SET
from hera.parser import evaluate_ifdefs, parse


def valid(text, *, warnings=False):
    program, messages = parse(text)
    assert not messages.errors, messages.errors[0]
    if not warnings:
        assert not messages.warnings, messages.warnings[0]
    return program


def invalid(text):
    program, messages = parse(text)
    return messages


def test_parse_single_op():
    program = valid("SET(R1, 42)")

    assert program == [SET(R(1), INT(42))]


def test_parse_has_locations():
    program = valid("SET(  R1,\n42)")

    op = program[0]
    assert isinstance(op, SET)
    assert op.loc.line == 1
    assert op.loc.column == 1

    assert op.tokens[0].location.line == 1
    assert op.tokens[0].location.column == 7

    assert op.tokens[1].location.line == 2
    assert op.tokens[1].location.column == 1


def test_parse_op_with_no_args():
    program = valid("RTI()")

    assert program == [RTI()]


def test_parse_multiple_ops():
    program = valid("INC(R4, 5)\nADD(R1, R2, R3)")

    assert program == [INC(R(4), INT(5)), ADD(R(1), R(2), R(3))]


def test_parse_label_starting_with_register_name():
    program = valid("LABEL(R1_INIT)")

    assert program == [LABEL(Token.Sym("R1_INIT"))]


def test_parse_octal_number():
    program = valid("SETLO(R1, 0o123)")

    assert program[0].args[1] == 0o123


def test_parse_hex_number():
    program = valid("SETHI(R1, 0xaBc)")

    assert program[0].args[1] == 0xABC


def test_parse_binary_number():
    program = valid("INC(R7, 0b10101)")

    assert program[0].args[1] == 0b10101


def test_parse_empty_program():
    program = valid("")

    assert len(program) == 0


def test_parse_single_line_comment():
    program = valid("// A comment")

    assert len(program) == 0


def test_parse_single_line_comment_with_ops():
    program = valid("SETLO(R1, 1) // A comment\nSETHI(R1, 1)")

    assert len(program) == 2
    assert program[0].name == "SETLO"
    assert program[1].name == "SETHI"


def test_parse_cpp_boilerplate():
    program = valid(
        """\
#include <HERA.h>

void HERA_main() {
    SET(R1, 42)
}
    """,
        warnings=True,
    )

    assert len(program) == 1
    assert program[0].name == "SET"


def test_parse_cpp_boilerplate_weird_whitespace_and_spelling():
    program = valid("#include <HERA.h>\nvoid   HeRA_mAin( \t)\n {\n\n}", warnings=True)

    assert program == []


def test_parse_empty_cpp_boilerplate():
    program = valid(
        """\
#include <HERA.h>

void HERA_main() {
}
    """,
        warnings=True,
    )

    assert len(program) == 0


def test_parse_ops_with_semicolons():
    program = valid("SET(R1, 1); SET(R2, 2)")

    assert len(program) == 2
    assert program[0].name == "SET"
    assert program[1].name == "SET"


def test_evaluate_ifdefs_with_simple_ifdef():
    program = evaluate_ifdefs(
        """
#ifdef HERA_PY
  SET(R1, 42)
#endif
    """
    )

    assert program.strip() == "SET(R1, 42)"


def test_evaluate_ifdefs_with_no_ifdefs():
    original = "Just some text.\nWith no ifdefs."
    program = evaluate_ifdefs(original)
    assert program == original


def test_evaluate_ifdefs_with_ifdef_and_else():
    program = evaluate_ifdefs(
        """
#ifdef HERA_PY
  SET(R1, 42)
#else
  R1 = 42;
#endif
    """
    )

    assert program.strip() == "SET(R1, 42)"


def test_evaluate_ifdefs_with_ifdef_and_else_with_leading_whitespace():
    program = evaluate_ifdefs(
        """
  #ifdef HERA_PY
    SET(R1, 42)
  #else
    R1 = 42;
  #endif
    """
    )

    assert program.strip() == "SET(R1, 42)"


def test_evaluate_ifdefs_with_ifndef():
    program = evaluate_ifdefs(
        """
#ifndef HERA_PY
  R1 = 42;
#else
  SET(R1, 42)
#endif
    """
    )

    assert program.strip() == "SET(R1, 42)"


def test_evaluate_ifdefs_with_ifdef_of_unknown_token():
    program = evaluate_ifdefs(
        """
#ifndef HERA_CPP
  SET(R1, 42)
#else
  R1 = 42;
#endif
    """
    )

    assert program.strip() == "SET(R1, 42)"


def test_evaluate_ifdefs_with_complex_program():
    program = evaluate_ifdefs(
        """
// Leading text should be included.
#ifdef HERA_PY
  // 1: This should be included.
  #ifdef HERA_CPP
    // 1: This should not be included.
    #else
    // 2: This should be included.
    #endif
  // 3: This should be included.
  #endif
// 4: This should be included.
#ifndef HERA_PY
  // 2: This should not be included.
  #else
  // 5: This should be included.
  #ifdef WHATEVER
    // 3: This should not be included.
    #else
    // 6: This should be included.
  #endif
  // 7: This should be included.
#endif
// Trailing text should be included.
    """
    )

    assert (
        program.strip()
        == """\
// Leading text should be included.

  // 1: This should be included.

    // 2: This should be included.

  // 3: This should be included.

// 4: This should be included.

  // 5: This should be included.

    // 6: This should be included.

  // 7: This should be included.

// Trailing text should be included."""
    )


def SYM(s):
    return Token(Token.SYMBOL, s)


def INT(x):
    return Token(Token.INT, x)


def R(i):
    return Token(Token.REGISTER, i)
