from .utils import preprocess_program_helper


def test_preprocess_simple_program(capsys):
    preprocess_program_helper("SET(R1, 10)")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        captured.err
        == """\

  0000  SETLO(R1, 10)
  0001  SETHI(R1, 0)
"""
    )


def test_preprocess_data(capsys):
    preprocess_program_helper('LP_STRING("hello")')

    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        captured.err
        == """\

[DATA]
  LP_STRING("hello")
"""
    )


def test_preprocess_data_and_code(capsys):
    preprocess_program_helper('DLABEL(s) LP_STRING("hello") SET(R1, s)')

    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        captured.err
        == """\

[DATA]
  LP_STRING("hello")

[CODE]
  0000  SETLO(R1, 1)
  0001  SETHI(R1, 192)
"""
    )


def test_preprocess_character_literal(capsys):
    preprocess_program_helper("SET(R1, 'A')")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "\n  0000  SETLO(R1, 65)\n  0001  SETHI(R1, 0)\n"
