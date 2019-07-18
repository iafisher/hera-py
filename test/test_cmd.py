import pytest
import re
from io import StringIO
from unittest.mock import patch

from hera.data import Settings, VOLUME_VERBOSE
from hera.main import dump_state, main
from hera.vm import VirtualMachine


def test_main_non_existent_file(capsys):
    with pytest.raises(SystemExit):
        main(["unicorn.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == 'Error: file "unicorn.hera" does not exist.\n'


def test_main_preprocess_non_existent_file(capsys):
    with pytest.raises(SystemExit):
        main(["preprocess", "unicorn.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == 'Error: file "unicorn.hera" does not exist.\n'


def test_main_debug(capsys):
    # Just making sure we can invoke the debugger from the command-line, not testing
    # any of the debugger's functionality.
    with patch("sys.stdin", StringIO("quit")):
        main(["debug", "test/assets/cs240/factorial.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""


def test_main_with_short_version_flag(capsys):
    with pytest.raises(SystemExit):
        main(["-v"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert re.match(r"^hera-py [0-9.]+ for HERA version [0-9.]+$", captured.out)


def test_main_with_long_version_flag(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert re.match(r"^hera-py [0-9.]+ for HERA version [0-9.]+$", captured.out)


def test_main_with_version_flag_and_other_flags(capsys):
    with pytest.raises(SystemExit):
        main(["--version", "main.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        captured.err == "--version may not be combined with other flags or commands.\n"
    )


def test_main_with_help_flag_and_other_flags(capsys):
    with pytest.raises(SystemExit):
        main(["--help", "main.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "--help may not be combined with other flags or commands.\n"


def test_main_with_multiple_positional_args(capsys):
    with pytest.raises(SystemExit):
        main(["a.hera", "b.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Too many file paths supplied.\n"


def test_main_with_no_positional_args(capsys):
    with pytest.raises(SystemExit):
        main([])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "No file path supplied.\n"


def test_main_with_short_quiet_flag(capsys):
    with patch("sys.stdin", StringIO("SET(R1, 42)")):
        main(["-q", "-"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "\n"


def test_main_with_long_quiet_flag(capsys):
    with patch("sys.stdin", StringIO("SET(R1, 42)")):
        main(["--quiet", "-"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "\n"


def test_main_with_quiet_and_verbose_flags(capsys):
    with pytest.raises(SystemExit):
        main(["--quiet", "--verbose", "main.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "--quiet and --verbose are incompatible.\n"


def test_main_preprocess_and_debug_with_big_stack_flag(capsys):
    with pytest.raises(SystemExit):
        main(["--big-stack", "preprocess", "main.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "--big-stack is not compatible with the chosen mode.\n"


def test_main_preprocess_with_warn_return_off_flag(capsys):
    with pytest.raises(SystemExit):
        main(["--warn-return-off", "preprocess", "main.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "--warn-return-off is not compatible with the chosen mode.\n"


def test_main_with_verbose_flag(capsys):
    with patch("sys.stdin", StringIO("SET(R1, 42)")):
        main(["--verbose", "-"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert (
        captured.err
        == """\


Virtual machine state after execution:
    R1  = 0x002a = 42 = '*'
    R2  = 0x0000 = 0
    R3  = 0x0000 = 0
    R4  = 0x0000 = 0
    R5  = 0x0000 = 0
    R6  = 0x0000 = 0
    R7  = 0x0000 = 0
    R8  = 0x0000 = 0
    R9  = 0x0000 = 0
    R10 = 0x0000 = 0
    R11 = 0x0000 = 0
    R12 = 0x0000 = 0
    R13 = 0x0000 = 0
    R14 = 0x0000 = 0
    R15 = 0x0000 = 0

    Carry-block flag is OFF
    Carry flag is OFF
    Overflow flag is OFF
    Zero flag is OFF
    Sign flag is OFF
"""
    )


def test_main_with_big_stack_flag(capsys):
    program = "DLABEL(X)\nSET(R1, X)"
    with patch("sys.stdin", StringIO(program)):
        main(["--big-stack", "-"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "R1  = 0xc167" in captured.err


def test_main_with_no_debug_flag(capsys):
    with pytest.raises(SystemExit):
        program = "print_reg(R1)"
        with patch("sys.stdin", StringIO(program)):
            main(["--no-debug-ops", "-"])

    captured = capsys.readouterr()
    assert (
        captured.err
        == """\

Error: debugging instructions disallowed with --no-debug-ops flag, line 1 col 1 of <stdin>

  print_reg(R1)
  ^

"""
    )


def test_main_with_code_flag(capsys):
    with pytest.raises(SystemExit):
        main(["--code", "whatever.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "--code is not compatible with the chosen mode.\n"


def test_main_with_data_flag(capsys):
    with pytest.raises(SystemExit):
        main(["--data", "whatever.hera"])

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "--data is not compatible with the chosen mode.\n"


def test_no_ANSI_color_when_stderr_is_not_tty():
    buf = StringIO()
    with patch("sys.stderr", buf):
        with patch("sys.stdin", StringIO(")")):
            with pytest.raises(SystemExit):
                main(["-"])

    assert (
        buf.getvalue()
        == """\

Error: expected HERA operation or #include, line 1 col 1 of <stdin>

  )
  ^

"""
    )


def test_main_with_init_flag(capsys):
    with patch("sys.stdin", StringIO("NOP()")):
        main(["-", "--init=r1=4, r2=5"])

    captured = capsys.readouterr().err
    assert "R1  = 0x0004 = 4" in captured
    assert "R2  = 0x0005 = 5" in captured


def test_main_with_init_flag_withg_different_syntax(capsys):
    with patch("sys.stdin", StringIO("NOP()")):
        main(["-", "--init", "r1=4, r2=5"])

    captured = capsys.readouterr().err
    assert "R1  = 0x0004 = 4" in captured
    assert "R2  = 0x0005 = 5" in captured


def test_main_with_dash_to_separate_arguments(capsys):
    with pytest.raises(SystemExit):
        main(["debug", "--", "--version"])

    captured = capsys.readouterr()
    assert captured.out == ""
    # Make sure we get a "file not found" error and not a "cannot use --version with
    # debug subcommand" error, which would indicate that the dash separator was not
    # being interpreted correctly.
    assert 'file "--version" does not exist' in captured.err


def test_credits_flag(capsys):
    with pytest.raises(SystemExit):
        main(["--credits"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Ian Fisher" in captured.out


def test_throttle_flag(capsys):
    with patch("sys.stdin", StringIO("LABEL(start); BR(start)")):
        main(["--throttle", "100", "-"])

    captured = capsys.readouterr()
    assert "Program throttled after 100 instructions." in captured.err


def test_dump_state(capsys):
    dump_state(VirtualMachine(), Settings(volume=VOLUME_VERBOSE))

    assert (
        capsys.readouterr().err
        == """\

Virtual machine state after execution:
    R1  = 0x0000 = 0
    R2  = 0x0000 = 0
    R3  = 0x0000 = 0
    R4  = 0x0000 = 0
    R5  = 0x0000 = 0
    R6  = 0x0000 = 0
    R7  = 0x0000 = 0
    R8  = 0x0000 = 0
    R9  = 0x0000 = 0
    R10 = 0x0000 = 0
    R11 = 0x0000 = 0
    R12 = 0x0000 = 0
    R13 = 0x0000 = 0
    R14 = 0x0000 = 0
    R15 = 0x0000 = 0

    Carry-block flag is OFF
    Carry flag is OFF
    Overflow flag is OFF
    Zero flag is OFF
    Sign flag is OFF
"""
    )
