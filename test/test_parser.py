import pytest
from unittest.mock import patch

from hera.data import Op
from hera.parser import parse, parse_file, replace_escapes


def test_replace_escapes_with_one_escape():
    assert replace_escapes("abc\\ndef") == "abc\ndef"


def test_replace_escapes_with_many_escapes():
    assert replace_escapes('\\\\\\n\\ta\\"') == '\\\n\ta"'


def test_replace_escapes_with_invalid_escape():
    assert replace_escapes("\\c") == "\\c"


def test_parse_op():
    assert parse("SETLO(R1, 4)") == [Op("SETLO", ["R1", 4])]


def test_parse_op_with_label():
    parsed = parse("SETLO(R1, top)")
    assert parsed == [Op("SETLO", ["R1", "top"])]
    assert parsed[0].args[0].type == "REGISTER"
    assert parsed[0].args[1].type == "SYMBOL"


def test_parse_string():
    parsed = parse('LP_STRING("hello")')
    assert parsed == [Op("LP_STRING", ["hello"])]
    assert parsed[0].args[0].type == "STRING"


def test_parse_empty_string():
    assert parse('LP_STRING("")') == [Op("LP_STRING", [""])]


def test_parse_string_with_escapes():
    assert parse('LP_STRING("multiline\\nstring with quotes: \\"\\"")') == [
        Op("LP_STRING", ['multiline\nstring with quotes: ""'])
    ]


def test_parse_character_literal():
    assert parse("SETLO(R1, 'X')") == [Op("SETLO", ["R1", 88])]


def test_parse_character_literal_with_escape():
    assert parse("SETLO(R1, '\\t')") == [Op("SETLO", ["R1", 9])]


def test_parse_signed_number():
    assert parse("SETLO(R1, -12)") == [Op("SETLO", ["R1", -12])]


def test_parse_hex_number():
    assert parse("SETLO(R4, 0x5f)") == [Op("SETLO", ["R4", 0x5F])]


def test_parse_negative_hex_number():
    assert parse("SETLO(R7, -0x2B)") == [Op("SETLO", ["R7", -0x2B])]


def test_parse_binary_number():
    assert parse("SETLO(R5, 0b10110)") == [Op("SETLO", ["R5", 22])]


def test_parse_negative_binary_number():
    assert parse("SETLO(R5, -0b10110)") == [Op("SETLO", ["R5", -22])]


def test_parse_octal_number():
    assert parse("SETLO(R3, 0o173)") == [Op("SETLO", ["R3", 123])]


def test_parse_negative_octal_number():
    assert parse("SETLO(R3, -0o173)") == [Op("SETLO", ["R3", -123])]


def test_parse_octal_number_without_o():
    assert parse("SETLO(R3, 0173)") == [Op("SETLO", ["R3", 123])]


def test_parse_label_starting_with_register_name():
    assert parse("LABEL(R1_INIT)") == [Op("LABEL", ["R1_INIT"])]


def test_parse_single_line_comment():
    assert parse("SETLO(R1, 0)  // R1 <- 0") == [Op("SETLO", ["R1", 0])]


def test_parse_hera_boilerplate():
    assert parse(
        "#include <HERA.h>\nvoid HERA_main() {SETLO(R1, 42)}", expand_includes=False
    ) == [Op("#include", ["<HERA.h>"]), Op("SETLO", ["R1", 42])]


def test_parse_hera_boilerplate_weird_whitespace_and_spelling():
    assert parse(
        "#include <HERA.h>\nvoid   HeRA_mAin( \t)\n {\n\n}", expand_includes=False
    ) == [Op("#include", ["<HERA.h>"])]


def test_parse_hera_boilerplate_no_includes():
    assert parse("void HERA_main() {SETLO(R1, 42)}") == [Op("SETLO", ["R1", 42])]


def test_parse_hera_boilerplate_gives_warning():
    with patch("hera.utils._emit_msg") as mock_emit_warning:
        parse("void HERA_main() {SETLO(R1, 42)}")
        assert mock_emit_warning.call_count == 1
        assert "Warning" in mock_emit_warning.call_args[0][0]
        assert "HERA_main" in mock_emit_warning.call_args[0][0]
        assert "not necessary" in mock_emit_warning.call_args[0][0]


def test_parse_another_single_line_comments():
    program = """\
// Single-line comment
SETLO(R9, 42)
    """
    assert parse(program) == [Op("SETLO", ["R9", 42])]


def test_parse_multiline_comment():
    program = """\
/* Starts on this line
   ends on this one */
SETLO(R1, 1)
    """
    assert parse(program) == [Op("SETLO", ["R1", 1])]


def test_parse_include_amidst_instructions():
    program = 'SETLO(R1, 42)\n#include "whatever"\n'
    assert parse(program, expand_includes=False) == [
        Op("SETLO", ["R1", 42]),
        Op("#include", ['"whatever"']),
    ]


def test_parse_missing_comma():
    with pytest.raises(SystemExit):
        parse("ADD(R1, R2 R3)")


def test_parse_missing_parenthesis():
    with pytest.raises(SystemExit):
        parse("LSL8(R1, R1")


def test_parse_missing_end_quote():
    with pytest.raises(SystemExit):
        parse('LP_STRING("forgot to close my string)')


def test_parse_exception_has_line_number(capsys):
    program = "SETLO(R1, 10)\nSETHI(R1, 255)\nLSL(R1 R1)"
    with pytest.raises(SystemExit):
        parse(program)

    captured = capsys.readouterr().err
    assert "unexpected character" in captured
    assert "line 3 col 8 of <string>" in captured


def test_parse_expands_include():
    assert parse_file("test/assets/include/simple.hera", expand_includes=True) == [
        Op("BR", ["end_of_add"]),
        Op("LABEL", ["add"]),
        Op("ADD", ["R3", "R1", "R2"]),
        Op("RETURN", ["R12", "R13"]),
        Op("LABEL", ["end_of_add"]),
        Op("SET", ["R1", 20]),
        Op("SET", ["R2", 22]),
        Op("CALL", ["R12", "add"]),
    ]
