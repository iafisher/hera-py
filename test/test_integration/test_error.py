import pytest

from hera.main import execute_program, main
from hera.vm import VirtualMachine


def test_error_message_for_missing_comma(capsys):
    with pytest.raises(SystemExit):
        # SETLO(R1 40)
        execute_program("test/assets/error/missing_comma.hera")

    captured = capsys.readouterr()
    assert "SETLO(R1 40)" in captured.err
    assert "line 1" in captured.err
    assert "col 10" in captured.err


def test_error_message_for_invalid_register(capsys):
    with pytest.raises(SystemExit):
        # SET(R17, 65)
        execute_program("test/assets/error/invalid_register.hera")

    captured = capsys.readouterr()
    assert "SET(R17, 65)" in captured.err
    assert "line 1" in captured.err
    assert "col 5" in captured.err
    # Make sure the caret is aligned properly.
    assert "      ^" in captured.err
    assert "R17" in captured.err
    assert "not a valid register" in captured.err


def test_error_message_for_invalid_register_with_weird_syntax(capsys):
    with pytest.raises(SystemExit):
        # SET(
        # 	R17,
        # 	65)
        execute_program("test/assets/error/invalid_register_weird.hera")

    captured = capsys.readouterr()
    assert "\tR17" in captured.err
    assert "SET(" not in captured.err
    assert "65" not in captured.err
    assert "line 2" in captured.err
    assert "col 2" in captured.err
    # Make sure the caret is aligned properly.
    assert "  \t^" in captured.err
    assert "not a valid register" in captured.err


def test_multiple_error_messages(capsys):
    with pytest.raises(SystemExit):
        # ADD(R1, 10)
        # INC(R4)
        execute_program("test/assets/error/multiple_errors.hera")

    captured = capsys.readouterr()
    assert "ADD" in captured.err
    assert "too few" in captured.err
    assert "not a register" in captured.err
    assert "line 1" in captured.err
    assert "INC" in captured.err
    assert "line 2" in captured.err


def test_dskip_overflow_program(capsys):
    vm = VirtualMachine()
    with pytest.raises(SystemExit):
        main(["test/assets/error/dskip_overflow.hera"], vm)

    captured = capsys.readouterr()
    assert "DSKIP(0xFFFF)" in captured.err
    assert "line 1" in captured.err
