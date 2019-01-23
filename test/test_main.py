import pytest
import re
from io import StringIO
from unittest.mock import patch

from hera.data import Op
from hera.main import dump_state, main, main_preprocess, program_to_string
from hera.vm import VirtualMachine


def test_program_to_string():
    program = [
        Op("SET", ["R1", 20]),
        Op("SET", ["R2", 22]),
        Op("ADD", ["R3", "R1", "R2"]),
    ]
    assert program_to_string(program) == "SET(R1, 20)\nSET(R2, 22)\nADD(R3, R1, R2)"


def test_dump_state(capsys):
    dump_state(VirtualMachine(), verbose=True)

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


def test_main_preprocess(capsys):
    with patch("sys.stdin", StringIO("SET(R1, 10)")):
        main(["preprocess", "-"])

    assert capsys.readouterr().out == "\nSETLO(R1, 10)\nSETHI(R1, 0)\n"


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
    vm = VirtualMachine()

    with patch("sys.stdin", StringIO("SET(R1, 42)")):
        main(["-"], vm)

    assert vm.registers[1] == 42


def test_preprocess_from_stdin(capsys):
    with patch("sys.stdin", StringIO("SET(R1, 42)")):
        main(["preprocess", "-"])

    captured = capsys.readouterr().out
    assert captured == "\nSETLO(R1, 42)\nSETHI(R1, 0)\n"


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
    assert captured.out == "\n"
    assert captured.err == ""


def test_main_with_long_quiet_flag(capsys):
    with patch("sys.stdin", StringIO("SET(R1, 42)")):
        main(["--quiet", "-"])

    captured = capsys.readouterr()
    assert captured.out == "\n"
    assert captured.err == ""


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
