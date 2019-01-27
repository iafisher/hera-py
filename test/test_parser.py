import os
import pytest

from hera.data import HERAError, Op
from hera.parser import parse, replace_escapes
from hera.utils import read_file


def helper(text, *, warnings=False, **kwargs):
    program, messages = parse(text, **kwargs)
    assert not messages.errors
    if not warnings:
        assert not messages.warnings
    return program


def test_replace_escapes_with_one_escape():
    assert replace_escapes("abc\\ndef") == "abc\ndef"


def test_replace_escapes_with_many_escapes():
    assert replace_escapes('\\\\\\n\\ta\\"') == '\\\n\ta"'


def test_replace_escapes_with_invalid_escape():
    with pytest.raises(HERAError):
        replace_escapes("\\c")


def test_parse_op():
    program = helper("SETLO(R1, 4)")

    assert program == [Op("SETLO", ["R1", 4])]


def test_parse_op_with_label():
    program = helper("SETLO(R1, top)")

    assert program == [Op("SETLO", ["R1", "top"])]
    assert program[0].args[0].type == "REGISTER"
    assert program[0].args[1].type == "SYMBOL"


def test_parse_string():
    program = helper('LP_STRING("hello")')

    assert program == [Op("LP_STRING", ["hello"])]
    assert program[0].args[0].type == "STRING"


def test_parse_empty_string():
    program = helper('LP_STRING("")')

    assert program == [Op("LP_STRING", [""])]


def test_parse_string_with_escapes():
    program = helper('LP_STRING("multiline\\nstring with quotes: \\"\\"")')

    assert program == [Op("LP_STRING", ['multiline\nstring with quotes: ""'])]


def test_parse_character_literal():
    program = helper("SETLO(R1, 'X')")

    assert program == [Op("SETLO", ["R1", 88])]


def test_parse_character_literal_with_escape():
    program = helper("SETLO(R1, '\\t')")

    assert program == [Op("SETLO", ["R1", 9])]


def test_parse_signed_number():
    program = helper("SETLO(R1, -12)")

    assert program == [Op("SETLO", ["R1", -12])]


def test_parse_hex_number():
    program = helper("SETLO(R4, 0x5f)")

    assert program == [Op("SETLO", ["R4", 0x5F])]


def test_parse_negative_hex_number():
    program = helper("SETLO(R7, -0x2B)")

    assert program == [Op("SETLO", ["R7", -0x2B])]


def test_parse_binary_number():
    program = helper("SETLO(R5, 0b10110)")

    assert program == [Op("SETLO", ["R5", 22])]


def test_parse_negative_binary_number():
    program = helper("SETLO(R5, -0b10110)")

    assert program == [Op("SETLO", ["R5", -22])]


def test_parse_octal_number():
    program = helper("SETLO(R3, 0o173)")

    assert program == [Op("SETLO", ["R3", 123])]


def test_parse_negative_octal_number():
    program = helper("SETLO(R3, -0o173)", warnings=True)

    assert program == [Op("SETLO", ["R3", -123])]


def test_parse_octal_number_without_o():
    program = helper("SETLO(R3, 0173)", warnings=True)

    assert program == [Op("SETLO", ["R3", 123])]


def test_parse_label_starting_with_register_name():
    program = helper("LABEL(R1_INIT)")

    assert program == [Op("LABEL", ["R1_INIT"])]


def test_parse_single_line_comment():
    program = helper("SETLO(R1, 0)  // R1 <- 0")

    assert program == [Op("SETLO", ["R1", 0])]


def test_parse_hera_boilerplate():
    program = helper(
        "#include <HERA.h>\nvoid HERA_main() {SETLO(R1, 42)}", warnings=True
    )

    assert program == [Op("SETLO", ["R1", 42])]


def test_parse_hera_boilerplate_weird_whitespace_and_spelling():
    program = helper("#include <HERA.h>\nvoid   HeRA_mAin( \t)\n {\n\n}", warnings=True)

    assert program == []


def test_parse_hera_boilerplate_no_includes():
    program = helper("void HERA_main() {SETLO(R1, 42)}", warnings=True)

    assert program == [Op("SETLO", ["R1", 42])]


def test_parse_hera_boilerplate_gives_warning():
    program, messages = parse("void HERA_main() {SETLO(R1, 42)}")

    assert len(messages.errors) == 0
    assert len(messages.warnings) == 1
    assert (
        messages.warnings[0][0]
        == "void HERA_main() { ... } is not necessary for hera-py"
    )


def test_parse_include_hera_dot_h_gives_warning():
    program, messages = parse("#include <HERA.h> SETLO(R1, 42)")

    assert len(program) == 1
    assert len(messages.warnings) == 1
    assert messages.warnings[0][0] == "#include <HERA.h> is not necessary for hera-py"
    assert messages.warnings[0][1] is not None


def test_parse_another_single_line_comments():
    text = """\
// Single-line comment
SETLO(R9, 42)
    """
    program = helper(text)

    assert program == [Op("SETLO", ["R9", 42])]


def test_parse_multiline_comment():
    text = """\
/* Starts on this line
   ends on this one */
SETLO(R1, 1)
    """
    program = helper(text)

    assert program == [Op("SETLO", ["R1", 1])]


def test_parse_missing_comma():
    program, messages = parse("ADD(R1, R2 R3)")

    assert program == []
    assert len(messages.errors) == 1


def test_parse_missing_parenthesis():
    program, messages = parse("LSL8(R1, R1")

    assert program == []
    assert len(messages.errors) == 1


def test_parse_missing_end_quote():
    program, messages = parse('LP_STRING("forgot to close my string)')

    assert program == []
    assert len(messages.errors) == 1


def test_parse_exception_has_line_number():
    program, messages = parse("SETLO(R1, 10)\nSETHI(R1, 255)\nLSL(R1 R1)")

    assert program == []
    assert len(messages.errors) == 1
    assert "unexpected character" in messages.errors[0][0]

    loc = messages.errors[0][1]
    assert loc is not None
    assert loc.line == 3
    assert loc.column == 8
    assert loc.path == "<string>"


def test_parse_expands_include():
    path = "test/assets/include/simple.hera"
    program = helper(read_file(path), path=path)

    assert program == [
        Op("BR", ["end_of_add"]),
        Op("LABEL", ["add"]),
        Op("ADD", ["R3", "R1", "R2"]),
        Op("RETURN", ["R12", "R13"]),
        Op("LABEL", ["end_of_add"]),
        Op("SET", ["R1", 20]),
        Op("SET", ["R2", 22]),
        Op("CALL", ["R12", "add"]),
    ]


def test_parse_with_angle_bracket_include():
    os.environ["HERA_C_DIR"] = "/some/impossible/path"
    program, messages = parse("#include <unicorn.hera>")
    del os.environ["HERA_C_DIR"]

    assert program == []
    assert len(messages.errors) == 1
    assert (
        messages.errors[0][0]
        == 'file "/some/impossible/path/unicorn.hera" does not exist'
    )
