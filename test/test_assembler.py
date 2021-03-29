from io import StringIO
from unittest.mock import patch

from hera.main import main


def test_assemble_set_inc(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/set_inc.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/set_inc.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_binary_op(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/binary_op.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/binary_op.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_branch(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/branch.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/branch.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_labelled_branch(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/branch_label.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/branch_label.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_relative_branch(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/rel_branch.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/rel_branch.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_flag(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/flag.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/flag.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_shift(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/shift.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/shift.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_misc(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/misc.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/misc.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_custom_opcode(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/opcode.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/opcode.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_debug_op(capsys):
    main(["assemble", "--code", "--stdout", "test/assets/asm/debug.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/debug.hera.lcode") as f:
        assert captured.out == f.read()


def test_assemble_data(capsys):
    main(["assemble", "--data", "--stdout", "test/assets/asm/data.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/data.hera.ldata") as f:
        assert captured.out == f.read()


def test_assemble_data_with_big_stack(capsys):
    main(["assemble", "--data", "--stdout", "--big-stack", "test/assets/asm/data.hera"])

    captured = capsys.readouterr()
    assert captured.err == ""

    with open("test/assets/asm/data_big_stack.hera.ldata") as f:
        assert captured.out == f.read()


def test_assemble_code_and_data_together(capsys):
    with patch("sys.stdin", StringIO("SET(R1, 42)")):
        main(["assemble", "--stdout", "-"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert (
        captured.out
        == """\

[DATA]
  49152*0
  c001

[CODE]
  e12a
  f100
"""
    )
