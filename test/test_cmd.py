import pytest
import re
from io import StringIO
from unittest.mock import patch

from hera.data import Settings, VOLUME_VERBOSE
from hera.main import dump_state, main
from hera.vm import VirtualMachine


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


def test_main_non_existent_file(capsys):
    with pytest.raises(SystemExit):
        main("unicorn.hera")

    assert capsys.readouterr().err == 'Error: file "unicorn.hera" does not exist\n'


def test_main_preprocess_non_existent_file(capsys):
    with pytest.raises(SystemExit):
        main(["preprocess", "unicorn.hera"])

    assert capsys.readouterr().err == 'Error: file "unicorn.hera" does not exist\n'


def test_main_debug(capsys):
    # Just making sure we can invoke the debugger from the command-line, not testing
    # any of the debugger's functionality.
    with patch("sys.stdin", StringIO("quit")):
        main(["debug", "test/assets/cs240/factorial.hera"])


def test_execute_from_stdin():
    with patch("sys.stdin", StringIO("SET(R1, 42)")):
        vm = main(["-"])

    assert vm.registers[1] == 42


def test_main_with_short_version_flag(capsys):
    with pytest.raises(SystemExit):
        main(["-v"])

    captured = capsys.readouterr().out
    assert re.match(r"^hera-py [0-9.]+ for HERA version [0-9.]+$", captured)


def test_main_with_long_version_flag(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])

    captured = capsys.readouterr().out
    assert re.match(r"^hera-py [0-9.]+ for HERA version [0-9.]+$", captured)


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


def test_main_with_verbose_flag(capsys):
    with patch("sys.stdin", StringIO("SET(R1, 42)")):
        main(["--verbose", "-"])

    captured = capsys.readouterr().err
    assert (
        captured
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

    captured = capsys.readouterr().err
    assert "R1  = 0xc167" in captured


def test_no_ANSI_color_when_stderr_is_not_tty():
    buf = StringIO()
    with patch("sys.stderr", buf):
        with patch("sys.stdin", StringIO(")")):
            with pytest.raises(SystemExit):
                main(["-"])

    assert (
        buf.getvalue()
        == """\

Error: unexpected character, line 1 col 1 of <stdin>

  )
  ^

"""
    )
