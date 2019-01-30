import pytest

from .utils import execute_program_helper


def test_warning_for_interrupt_instructions(capsys):
    program = """\
// These should give warnings.
SWI(10)
RTI()

// These should not give warnings (already given).
SWI(10)
RTI()
    """
    execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Warning: SWI is a no-op in this simulator, line 2 col 1 of <stdin>

  SWI(10)
  ^

Warning: RTI is a no-op in this simulator, line 3 col 1 of <stdin>

  RTI()
  ^


Virtual machine state after execution:
    R1 through R10 are all zero.

    All flags are OFF

2 warnings emitted.
"""
    )


def test_warning_for_stack_overflow(capsys):
    program = "SET(R1, 0xC002)\nADD(SP, SP, R1)\nDEC(SP, 10)\nINC(SP, 30)"
    execute_program_helper(program)

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Warning: stack has overflowed into data segment, line 2 col 1 of <stdin>

  ADD(SP, SP, R1)
  ^


Virtual machine state after execution:
    R1  = 0xc002 = 49154 = -16382

    Carry-block flag is OFF
    Carry flag is OFF
    Overflow flag is OFF
    Zero flag is OFF
    Sign flag is ON

1 warning emitted.
"""
    )


@pytest.mark.skip("not ready")
def test_warning_for_zero_prefixed_octal(capsys):
    execute_program_helper("SET(R1, 016)\nSET(R2, 017)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Warning: consider using "0o" prefix for octal numbers, line 1 col 9 of <stdin>

  SET(R1, 016)
          ^

Warning: consider using "0o" prefix for octal numbers, line 2 col 9 of <stdin>

  SET(R2, 017)
          ^


Virtual machine state after execution:
    R1  = 0x000e = 14
    R2  = 0x000f = 15

    All flags are OFF

2 warnings emitted.
"""
    )


def test_warning_for_R11_with_NOT(capsys):
    execute_program_helper("SET(R11, 5)\nNOT(R1, R11)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Warning: don't use R11 with NOT, line 2 col 9 of <stdin>

  NOT(R1, R11)
          ^


Virtual machine state after execution:
    R1 through R10 are all zero.

    Carry-block flag is OFF
    Carry flag is OFF
    Overflow flag is OFF
    Zero flag is ON
    Sign flag is OFF

1 warning emitted.
"""
    )


def test_warning_for_improper_register_with_CALL(capsys):
    execute_program_helper("CALL(R11, l)\nLABEL(l)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Warning: first argument to CALL should be R12, line 1 col 6 of <stdin>

  CALL(R11, l)
       ^


Virtual machine state after execution:
    R1 through R10 are all zero.

    All flags are OFF

1 warning emitted.
"""
    )


def test_warning_for_improper_first_register_with_RETURN(capsys):
    execute_program_helper("RETURN(R11, R13)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Warning: first argument to RETURN should be R12, line 1 col 8 of <stdin>

  RETURN(R11, R13)
         ^


Virtual machine state after execution:
    R1 through R10 are all zero.

    All flags are OFF

1 warning emitted.
"""
    )


def test_warning_for_improper_second_register_with_RETURN(capsys):
    execute_program_helper("RETURN(R12, R11)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Warning: second argument to RETURN should be R13, line 1 col 13 of <stdin>

  RETURN(R12, R11)
              ^


Virtual machine state after execution:
    R1 through R10 are all zero.

    All flags are OFF

1 warning emitted.
"""
    )


def test_warning_for_unnecessary_include(capsys):
    execute_program_helper("#include <HERA.h>")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\

Warning: #include <HERA.h> is not necessary for hera-py, line 1 col 11 of <stdin>

  #include <HERA.h>
            ^


Virtual machine state after execution:
    R1 through R10 are all zero.

    All flags are OFF

1 warning emitted.
"""
    )
