from hera.data import Op, Token, TOKEN
from hera.parser import parse


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

    assert program == [Op(SYM("SET"), [R(1), INT(42)])]


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

    assert program == [Op("RTI", [])]


def test_parse_multiple_ops():
    program = valid("INC(R4, 5)\nADD(R1, R2, R3)")

    assert program == [Op("INC", [4, 5]), Op("ADD", [1, 2, 3])]


def test_parse_label_starting_with_register_name():
    program = valid("LABEL(R1_INIT)")

    assert program == [Op("LABEL", ["R1_INIT"])]


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


def SYM(s):
    return Token(TOKEN.SYMBOL, s)


def INT(x):
    return Token(TOKEN.INT, x)


def R(i):
    return Token(TOKEN.REGISTER, i)
