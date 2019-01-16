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
	R1  = 0xc002 = 49154

	Carry-block flag is OFF
	Carry flag is OFF
	Overflow flag is OFF
	Zero flag is OFF
	Sign flag is ON

1 warning emitted.
"""
    )


def test_warning_for_zero_prefixed_octal(capsys):
    execute_program_helper("SET(R1, 016)\nSET(R2, 017)")

    captured = capsys.readouterr().err
    assert (
        captured
        == """\
Warning: consider using "0o" prefix for octal numbers, line 1 col 9 of <stdin>

  SET(R1, 016)
          ^


Virtual machine state after execution:
	R1  = 0x000e = 14
	R2  = 0x000f = 15

	All flags are OFF

1 warning emitted.
"""
    )
