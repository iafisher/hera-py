import pytest
import re
from io import StringIO
from unittest.mock import patch

from hera.data import Op
from hera.main import dump_state, main, main_preprocess, op_to_string, program_to_string
from hera.vm import VirtualMachine


def test_op_to_string():
    assert op_to_string(Op("SET", ["R1", "top"])) == "SET(R1, top)"


def test_op_to_string_with_integer():
    assert op_to_string(Op("INC", ["R7", 12])) == "INC(R7, 12)"


def test_program_to_string():
    program = [
        Op("SET", ["R1", 20]),
        Op("SET", ["R2", 22]),
        Op("ADD", ["R3", "R1", "R2"]),
    ]
    assert program_to_string(program) == "SET(R1, 20)\nSET(R2, 22)\nADD(R3, R1, R2)"


def test_dump_state(capsys):
    dump_state(VirtualMachine(), verbose=True)

    captured = capsys.readouterr()
    assert "R1  = 0x0000 = 0" in captured.err
    assert "R7  = 0x0000 = 0" in captured.err
    assert "R14 = 0x0000 = 0" in captured.err
    assert "Zero flag is OFF" in captured.err
    assert "Sign flag is OFF" in captured.err
    assert "Overflow flag is OFF" in captured.err
    assert "Carry flag is OFF" in captured.err
    assert "Carry-block flag is OFF" in captured.err


def test_main_non_existent_file(capsys):
    with pytest.raises(SystemExit):
        main("unicorn.hera")

    assert 'file "unicorn.hera" does not exist' in capsys.readouterr().err


def test_main_preprocess(capsys):
    with patch("sys.stdin", StringIO("SET(R1, 10)")):
        main(["preprocess", "-"])

    assert capsys.readouterr().out == "\nSETLO(R1, 10)\nSETHI(R1, 0)\n"


def test_main_preprocess_non_existent_file(capsys):
    with pytest.raises(SystemExit):
        main_preprocess("unicorn.hera")

    assert 'file "unicorn.hera" does not exist' in capsys.readouterr().err


def test_main_debug(capsys):
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


def test_main_with_version_flag(capsys):
    with pytest.raises(SystemExit):
        main(["-v"])

    captured = capsys.readouterr().out
    assert re.match(r"^hera-py [0-9.]+ for HERA version [0-9.]+$", captured)


def test_main_with_quiet_flag(capsys):
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
