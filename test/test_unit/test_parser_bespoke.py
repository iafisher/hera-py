from hera.data import IntToken
from hera.lexer import TOKEN
from hera.parser_bespoke import parse


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

    assert len(program) == 1
    assert program[0].name == "SET"
    assert len(program[0].args) == 2
    assert program[0].args[0] == "R1"
    assert program[0].args[0].type == TOKEN.REGISTER
    assert program[0].args[1] == 42
    assert isinstance(program[0].args[1], IntToken)


def test_parse_has_locations():
    program = valid("SET(  R1,\n42)")

    op = program[0]
    assert op.name.location.line == 1
    assert op.name.location.column == 1

    assert op.args[0].location.line == 1
    assert op.args[0].location.column == 7

    assert op.args[1].location.line == 2
    assert op.args[1].location.column == 1


def test_parse_op_with_no_args():
    program = valid("RTI()")

    assert len(program) == 1
    assert program[0].name == "RTI"
    assert len(program[0].args) == 0


def test_parse_multiple_ops():
    program = valid("INC(R4, 5)\nADD(R1, R2, R3)")

    assert len(program) == 2
    assert program[0].name == "INC"
    assert program[0].args[0] == "R4"
    assert program[0].args[1] == 5

    assert program[1].name == "ADD"
    assert program[1].args[0] == "R1"
    assert program[1].args[1] == "R2"
    assert program[1].args[2] == "R3"


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
