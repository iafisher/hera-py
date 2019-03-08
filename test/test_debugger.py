import pytest
from unittest.mock import patch

from hera.data import Constant, DataLabel, DEFAULT_DATA_START, Label, Program, Settings
from hera.debugger import debug, Debugger, Shell
from hera.debugger.debugger import reverse_lookup_label
from hera.loader import load_program


@pytest.fixture
def shell():
    settings = Settings(color=False)
    return Shell(Debugger(SAMPLE_PROGRAM, settings), settings)


@pytest.fixture
def debugger():
    return Debugger(SAMPLE_PROGRAM, Settings())


def load_shell(program):
    settings = Settings(mode="debug")
    return Shell(Debugger(load_program(program, settings), settings), settings)


SAMPLE_PROGRAM = load_program(
    """\
// A comment
CONSTANT(N, 3)

SET(R1, N)
SET(R2, 39)
LABEL(add)
ADD(R3, R1, R2)
HALT()
""",
    Settings(mode="debug"),
)


def test_handle_break_prints_breakpoints(shell, capsys):
    shell.debugger.breakpoints[4] = "main.hera:7"
    shell.handle_command("break")

    assert capsys.readouterr().out == "main.hera:7\n"


def test_handle_break_prints_breakpoints_with_no_breakpoints_set(shell, capsys):
    shell.handle_command("break")

    assert capsys.readouterr().out == "No breakpoints set.\n"


def test_handle_break_sets_breakpoint(shell, capsys):
    assert len(shell.debugger.breakpoints) == 0

    shell.handle_command("break 5")

    assert len(shell.debugger.breakpoints) == 1
    assert 2 in shell.debugger.breakpoints
    assert shell.debugger.breakpoints[2] == "<string>:5"

    assert capsys.readouterr().out == "Breakpoint set in file <string>, line 5.\n"


def test_handle_break_with_dot(shell, capsys):
    shell.handle_command("break .")

    assert len(shell.debugger.breakpoints) == 1
    assert 0 in shell.debugger.breakpoints
    assert shell.debugger.breakpoints[0] == "<string>:4"

    assert capsys.readouterr().out == "Breakpoint set in file <string>, line 4.\n"


def test_handle_break_with_multiple_files(capsys):
    shell = load_shell('NOP()\n#include "test/assets/include/lib/add.hera"')
    shell.handle_command("break test/assets/include/lib/add.hera:1")

    assert len(shell.debugger.breakpoints) == 1
    assert 1 in shell.debugger.breakpoints
    assert shell.debugger.breakpoints[1] == "test/assets/include/lib/add.hera:1"

    assert (
        capsys.readouterr().out
        == "Breakpoint set in file test/assets/include/lib/add.hera, line 1.\n"
    )

    shell.handle_command("break 1")

    assert len(shell.debugger.breakpoints) == 2
    assert 0 in shell.debugger.breakpoints
    assert shell.debugger.breakpoints[0] == "<string>:1"

    assert capsys.readouterr().out == "Breakpoint set in file <string>, line 1.\n"


def test_handle_break_with_multiple_files_again(capsys):
    shell = load_shell('#include "test/assets/include/lib/add.hera"\nNOP()')

    shell.handle_command("break 1")

    assert len(shell.debugger.breakpoints) == 1
    assert 0 in shell.debugger.breakpoints

    captured = capsys.readouterr().out
    assert (
        captured == "Breakpoint set in file test/assets/include/lib/add.hera, line 1.\n"
    )


def test_handle_break_with_invalid_location(shell, capsys):
    shell.handle_command("break 1")

    assert len(shell.debugger.breakpoints) == 0
    assert capsys.readouterr().out == "Error: could not find corresponding line.\n"


def test_handle_break_with_unparseable_breakpoint(shell, capsys):
    shell.handle_command("break $$$")

    assert len(shell.debugger.breakpoints) == 0
    assert capsys.readouterr().out == "Error: could not locate label `$$$`.\n"


def test_handle_break_with_too_many_args(shell, capsys):
    shell.handle_command("break 1 2 3")

    assert len(shell.debugger.breakpoints) == 0
    assert capsys.readouterr().out == "break takes zero or one arguments.\n"


def test_handle_break_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_break") as mock_handle_break:
        shell.handle_command("b 7")
        assert mock_handle_break.call_count == 1

        args, kwargs = mock_handle_break.call_args
        assert len(args) == 1
        assert args[0] == ["7"]
        assert len(kwargs) == 0


def test_handle_clear(shell, capsys):
    shell.handle_command("break 4")
    capsys.readouterr()

    shell.handle_command("clear 4")

    assert len(shell.debugger.breakpoints) == 0

    captured = capsys.readouterr().out
    assert captured == "Cleared breakpoint in file <string>, line 4.\n"


def test_handle_clear_only_clears_one(shell):
    shell.handle_command("break 4")
    shell.handle_command("break 5")

    shell.handle_command("clear 4")

    assert len(shell.debugger.breakpoints) == 1
    assert 2 in shell.debugger.breakpoints


def test_handle_clear_with_multiple_args(shell, capsys):
    shell.handle_command("break 4")
    shell.handle_command("break 5")
    shell.handle_command("break 7")
    capsys.readouterr()

    shell.handle_command("clear 4 5")

    assert len(shell.debugger.breakpoints) == 1
    assert 4 in shell.debugger.breakpoints

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
Cleared breakpoint in file <string>, line 4.
Cleared breakpoint in file <string>, line 5.
"""
    )


def test_handle_clear_with_no_breakpoint(shell, capsys):
    shell.handle_command("clear 4")

    captured = capsys.readouterr().out
    assert captured == "No breakpoint at that location.\n"


def test_handle_clear_with_star_arg(shell, capsys):
    shell.handle_command("break 4")
    shell.handle_command("break 5")
    capsys.readouterr()

    shell.handle_command("clear *")

    assert len(shell.debugger.breakpoints) == 0

    captured = capsys.readouterr().out
    assert captured == "Cleared all breakpoints.\n"


def test_handle_clear_with_star_and_other_args(shell, capsys):
    shell.handle_command("break 4")
    shell.handle_command("break 5")
    capsys.readouterr()

    shell.handle_command("clear 4 * ???")

    assert len(shell.debugger.breakpoints) == 0

    captured = capsys.readouterr().out
    assert captured == "Cleared all breakpoints.\n"


def test_handle_clear_with_bad_arg(shell, capsys):
    shell.handle_command("clear ???")

    captured = capsys.readouterr().out
    assert captured == "Error: could not locate label `???`.\n"


def test_handle_clear_with_too_few_args(shell, capsys):
    shell.handle_command("clear")

    assert capsys.readouterr().out == "clear takes one or more arguments.\n"


def test_handle_clear_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_clear") as mock_handle_clear:
        shell.handle_command("cl 7")
        assert mock_handle_clear.call_count == 1

        args, kwargs = mock_handle_clear.call_args
        assert len(args) == 1
        assert args[0] == ["7"]
        assert len(kwargs) == 0


def test_handle_next(shell):
    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.pc == 0

    shell.handle_command("next")

    assert shell.debugger.vm.registers[1] == 3
    assert shell.debugger.vm.pc == 2


def test_handle_next_with_argument(shell):
    shell.handle_command("next 2")

    assert shell.debugger.vm.registers[1] == 3
    assert shell.debugger.vm.registers[2] == 39
    assert shell.debugger.vm.pc == 4


def test_handle_next_with_unparseable_argument(shell, capsys):
    shell.handle_command("next a")

    assert shell.debugger.vm.pc == 0
    assert capsys.readouterr().out == "Could not parse argument to next.\n"


def test_handle_next_with_HALT(shell, capsys):
    # Last instruction of SAMPLE_PROGRAM is a HALT operation.
    shell.debugger.vm.pc = 5

    shell.handle_command("next")

    assert shell.debugger.vm.pc == 5
    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_handle_next_with_function_call(capsys):
    shell = load_shell(
        """\
SET(R1, 4)
CALL(FP_alt, plus_two)
SET(R2, 5)
HALT()

LABEL(plus_two)
  INC(R1, 2)
  RETURN(FP_alt, PC_ret)
"""
    )
    shell.handle_command("n")
    capsys.readouterr()
    shell.handle_command("next")

    assert shell.debugger.vm.pc == 5
    assert shell.debugger.vm.registers[1] == 6
    assert shell.debugger.vm.registers[2] == 0

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>]

    2  CALL(FP_alt, plus_two)
->  3  SET(R2, 5)
    4  HALT()
"""
    )


def test_handle_next_with_recursive_function(capsys):
    shell = load_shell(
        """\
SET(R1, 9)
CALL(FP_alt, rec)
HALT()

LABEL(rec)
  MOVE(FP, SP)
  INC(SP, 2)
  STORE(PC_ret, 0, FP)
  STORE(FP_alt, 1, FP)

  CMP(R1, R0)
  BZ(end)
  INC(R2, 1)
  DEC(R1, 1)
  CALL(FP_alt, rec)
  LABEL(end)

  LOAD(PC_ret, 0, FP)
  LOAD(FP_alt, 1, FP)
  DEC(SP, 2)
  RETURN(FP_alt, PC_ret)
"""
    )
    shell.handle_command("n")
    capsys.readouterr()
    shell.handle_command("next")

    assert shell.debugger.vm.pc == 5
    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 9

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>]

     2  CALL(FP_alt, rec)
->   3  HALT()
     4
"""
    )


def test_handle_next_over_function_with_breakpoint(capsys):
    shell = load_shell(
        """\
CALL(FP_alt, foo)
HALT()

LABEL(foo)
  RETURN(FP_alt, PC_ret)
  """
    )
    shell.handle_command("break foo")
    capsys.readouterr()
    shell.handle_command("next")

    assert shell.debugger.vm.pc == 4

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>]

    4  LABEL(foo)
->  5    RETURN(FP_alt, PC_ret)
    6
"""
    )


def test_handle_next_after_end_of_program(shell, capsys):
    shell.debugger.vm.pc = 9000

    shell.handle_command("next")

    assert shell.debugger.vm.pc == 9000
    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_handle_next_with_too_many_args(shell, capsys):
    shell.handle_command("next 10 11")

    assert capsys.readouterr().out == "next takes zero or one arguments.\n"


def test_handle_next_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_next") as mock_handle_next:
        shell.handle_command("n")
        assert mock_handle_next.call_count == 1


def test_handle_continue_with_breakpoint(shell):
    shell.debugger.breakpoints[4] = ""

    shell.handle_command("continue")

    vm = shell.debugger.vm
    assert vm.registers[1] == 3
    assert vm.registers[2] == 39
    assert vm.registers[3] == 0
    assert vm.pc == 4

    # Make sure continuing again doesn't loop on the same instruction.
    shell.handle_command("continue")
    assert vm.pc == 5


def test_handle_continue_without_breakpoint(shell, capsys):
    shell.handle_command("continue")

    vm = shell.debugger.vm
    assert vm.registers[1] == 3
    assert vm.registers[2] == 39
    assert vm.registers[3] == 42
    assert vm.pc == 5
    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_handle_continue_with_too_many_args(shell, capsys):
    shell.handle_command("continue 10")

    assert capsys.readouterr().out == "continue takes no arguments.\n"


def test_handle_continue_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_continue") as mock_handle_continue:
        shell.handle_command("c")
        assert mock_handle_continue.call_count == 1


def test_handle_execute(shell):
    shell.handle_command("execute SET(R7, 42)")

    assert shell.debugger.vm.pc == 0
    assert shell.debugger.vm.registers[7] == 42


def test_handle_execute_with_branch(shell, capsys):
    shell.handle_command("execute BRR(10)")

    assert shell.debugger.vm.pc == 0
    assert capsys.readouterr().out == "execute cannot take branching operations.\n"


def test_handle_execute_with_data_statement(shell, capsys):
    shell.handle_command("execute INTEGER(42)")

    assert shell.debugger.vm.pc == 0
    assert capsys.readouterr().out == "execute cannot take data statements.\n"


def test_handle_execute_with_label(shell, capsys):
    shell.handle_command("execute LABEL(l)")

    assert shell.debugger.vm.pc == 0
    assert capsys.readouterr().out == "execute cannot take labels.\n"


def test_handle_execute_with_invalid_op(shell, capsys):
    shell.handle_command("execute ADD(R1, R2)")

    assert (
        capsys.readouterr().err
        == """\
Error: too few args to ADD (expected 3), line 1 col 1 of <string>

  ADD(R1, R2)
  ^

"""
    )


def test_handle_execute_with_no_args(shell, capsys):
    shell.handle_command("execute")

    assert capsys.readouterr().out == "execute takes one argument.\n"


def test_handle_goto_with_line_number(shell):
    shell.handle_command("goto 7")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 4


@pytest.mark.skip("Should this work?")
def test_handle_goto_with_line_number_not_on_operation(shell):
    # A line number that doesn't correspond to an actual operation.
    shell.handle_command("goto 6")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 4


def test_handle_goto_with_label(shell):
    shell.handle_command("goto add")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 4


def test_handle_goto_with_unknown_label(shell, capsys):
    shell.handle_command("goto whatever")

    assert capsys.readouterr().out == "Error: could not locate label `whatever`.\n"


def test_handle_goto_with_too_few_arguments(shell, capsys):
    shell.handle_command("goto")

    assert capsys.readouterr().out == "goto takes one argument.\n"


def test_handle_goto_with_too_many_arguments(shell, capsys):
    shell.handle_command("goto 1 2 3")

    assert capsys.readouterr().out == "goto takes one argument.\n"


def test_handle_goto_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_goto") as mock_handle_goto:
        shell.handle_command("g 10")
        assert mock_handle_goto.call_count == 1

        args, kwargs = mock_handle_goto.call_args
        assert len(args) == 1
        assert args[0] == ["10"]
        assert len(kwargs) == 0


def test_handle_info(shell, capsys):
    shell.handle_command("info")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
All registers set to zero.

All flags are off.

The call stack is empty.
"""
    )


def test_handle_info_with_registers_and_flags(shell, capsys):
    shell.debugger.vm.registers[7] = 42
    shell.debugger.vm.flag_carry_block = True
    shell.handle_command("info")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
R7 = 42, all other registers set to zero.

Carry-block flag is on, all other flags are off.

The call stack is empty.
"""
    )


def test_handle_info_with_all_registers_set(shell, capsys):
    shell.debugger.vm.registers = [1] * 16
    shell.handle_command("info")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
R1 = 1, R2 = 1, R3 = 1, R4 = 1, R5 = 1, R6 = 1, R7 = 1, R8 = 1, R9 = 1, R10 = 1, \
R11 = 1, R12 = 1, R13 = 1, R14 = 1, R15 = 1

All flags are off.

The call stack is empty.
"""
    )


def test_handle_info_with_symbols_arg(shell, capsys):
    shell.debugger.symbol_table["array"] = DataLabel(0xC001)
    shell.handle_command("info symbols")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
Constants: N (3)
Labels: add (<string>:6)
Data labels: array (0xc001)
"""
    )


def test_handle_info_with_registers_arg(shell, capsys):
    shell.handle_command("info registers")

    assert capsys.readouterr().out == "All registers set to zero.\n"


def test_handle_info_with_flags_arg(shell, capsys):
    shell.handle_command("info flags")

    assert capsys.readouterr().out == "All flags are off.\n"


def test_handle_info_with_multiple_args(shell, capsys):
    shell.handle_command("info symbols flags")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
Constants: N (3)
Labels: add (<string>:6)
Data labels: array (0xc001)

All flags are off.
"""
    )


def test_handle_info_with_stack_arg(capsys):
    shell = load_shell(
        """\
CALL(FP_alt, do_nothing)
HALT()

LABEL(do_nothing)
  RETURN(FP_alt, PC_ret)
"""
    )

    shell.handle_command("break do_nothing")
    shell.handle_command("continue")
    capsys.readouterr()
    shell.handle_command("info stack")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
Call stack (last call at bottom)
  do_nothing (<string>:5, called from <string>:1)
"""
    )


def test_handle_info_with_unrecognized_arg(shell, capsys):
    shell.handle_command("info symbols machine")

    captured = capsys.readouterr().out
    assert captured == "Error: unrecognized argument `machine`.\n"


def test_handle_info_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_info") as mock_handle_info:
        shell.handle_command("i")
        assert mock_handle_info.call_count == 1


def test_handle_list(shell, capsys):
    shell.handle_command("list")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>]

    1  // A comment
    2  CONSTANT(N, 3)
    3
->  4  SET(R1, N)
    5  SET(R2, 39)
    6  LABEL(add)
    7  ADD(R3, R1, R2)
"""
    )


def test_handle_list_with_context_arg(shell, capsys):
    shell.handle_command("list 1")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>]

    3
->  4  SET(R1, N)
    5  SET(R2, 39)
"""
    )


def test_handle_list_with_invalid_context_arg(shell, capsys):
    shell.handle_command("list abc")

    assert capsys.readouterr().out == "Could not parse argument to list.\n"


def test_handle_list_after_end_of_program(capsys):
    shell = load_shell("SET(R1, 42)")
    shell.handle_command("c")
    capsys.readouterr()
    shell.handle_command("list")

    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_handle_list_with_too_many_args(shell, capsys):
    shell.handle_command("list 1 2")

    assert capsys.readouterr().out == "list takes zero or one arguments.\n"


def test_handle_list_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_list") as mock_handle_list:
        shell.handle_command("l")
        assert mock_handle_list.call_count == 1


def test_handle_ll(shell, capsys):
    shell.handle_command("ll")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>]

    1  // A comment
    2  CONSTANT(N, 3)
    3
->  4  SET(R1, N)
    5  SET(R2, 39)
    6  LABEL(add)
    7  ADD(R3, R1, R2)
    8  HALT()
    9
"""
    )


def test_handle_ll_with_too_many_args(shell, capsys):
    shell.handle_command("ll 1")

    assert capsys.readouterr().out == "ll takes no arguments.\n"


def test_handle_ll_after_end_of_program(capsys):
    shell = load_shell("SET(R1, 42)")
    shell.handle_command("c")
    capsys.readouterr()
    shell.handle_command("ll")

    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_handle_abbreviated_ll(shell, capsys):
    with patch("hera.debugger.shell.Shell.handle_ll") as mock_handle_ll:
        shell.handle_command("ll")
        assert mock_handle_ll.call_count == 1


def test_handle_on(shell):
    shell.handle_command("on carry-block")
    shell.handle_command("on carry")
    shell.handle_command("on overflow")
    shell.handle_command("on sign")
    shell.handle_command("on zero")

    assert shell.debugger.vm.flag_carry_block
    assert shell.debugger.vm.flag_carry
    assert shell.debugger.vm.flag_overflow
    assert shell.debugger.vm.flag_sign
    assert shell.debugger.vm.flag_zero


def test_handle_on_with_abbreviated_flag(shell):
    shell.handle_command("on cb")
    shell.handle_command("on c")
    shell.handle_command("on v")
    shell.handle_command("on s")
    shell.handle_command("on z")

    assert shell.debugger.vm.flag_carry_block
    assert shell.debugger.vm.flag_carry
    assert shell.debugger.vm.flag_overflow
    assert shell.debugger.vm.flag_sign
    assert shell.debugger.vm.flag_zero


def test_handle_on_with_multiple_args(shell):
    shell.handle_command("on c v")

    assert shell.debugger.vm.flag_carry
    assert shell.debugger.vm.flag_overflow


def test_handle_on_with_invalid_flag(shell, capsys):
    shell.handle_command("on c y")

    assert capsys.readouterr().out == "Unrecognized flag: `y`.\n"


def test_handle_on_with_no_args(shell, capsys):
    shell.handle_command("on")

    assert capsys.readouterr().out == "on takes one or more arguments.\n"


def test_handle_off(shell):
    shell.debugger.vm.flag_carry_block = True
    shell.debugger.vm.flag_carry = True
    shell.debugger.vm.flag_overflow = True
    shell.debugger.vm.flag_sign = True
    shell.debugger.vm.flag_zero = True

    shell.handle_command("off carry-block")
    shell.handle_command("off carry")
    shell.handle_command("off overflow")
    shell.handle_command("off sign")
    shell.handle_command("off zero")

    assert not shell.debugger.vm.flag_carry_block
    assert not shell.debugger.vm.flag_carry
    assert not shell.debugger.vm.flag_overflow
    assert not shell.debugger.vm.flag_sign
    assert not shell.debugger.vm.flag_zero


def test_handle_off_with_abbreviated_flag(shell):
    shell.debugger.vm.flag_carry_block = True
    shell.debugger.vm.flag_carry = True
    shell.debugger.vm.flag_overflow = True
    shell.debugger.vm.flag_sign = True
    shell.debugger.vm.flag_zero = True

    shell.handle_command("off cb")
    shell.handle_command("off c")
    shell.handle_command("off v")
    shell.handle_command("off s")
    shell.handle_command("off z")

    assert not shell.debugger.vm.flag_carry_block
    assert not shell.debugger.vm.flag_carry
    assert not shell.debugger.vm.flag_overflow
    assert not shell.debugger.vm.flag_sign
    assert not shell.debugger.vm.flag_zero


def test_handle_off_with_multiple_args(shell):
    shell.debugger.vm.flag_carry = True
    shell.debugger.vm.flag_overflow = True

    shell.handle_command("off c v")

    assert not shell.debugger.vm.flag_carry
    assert not shell.debugger.vm.flag_overflow


def test_handle_off_with_invalid_flag(shell, capsys):
    shell.handle_command("off c y")

    assert capsys.readouterr().out == "Unrecognized flag: `y`.\n"


def test_handle_off_with_no_args(shell, capsys):
    shell.handle_command("off")

    assert capsys.readouterr().out == "off takes one or more arguments.\n"


def test_handle_restart(shell, capsys):
    shell.handle_command("n")
    shell.handle_command("n")
    capsys.readouterr()

    shell.handle_command("restart")

    vm = shell.debugger.vm
    assert vm.pc == 0
    assert vm.registers[1] == 0
    assert vm.registers[2] == 0
    assert (
        capsys.readouterr().out
        == """\
[<string>]

    3
->  4  SET(R1, N)
    5  SET(R2, 39)
"""
    )


def test_handle_restart_with_too_many_args(shell, capsys):
    shell.handle_command("restart 1")

    assert capsys.readouterr().out == "restart takes no arguments.\n"


def test_restart_cannot_be_abbreviated(shell, capsys):
    with patch("hera.debugger.shell.Shell.handle_restart") as mock_handle_restart:
        shell.handle_command("r")
        assert mock_handle_restart.call_count == 0


def test_handle_assign_to_register(shell):
    shell.handle_command("r12 = 10")

    assert shell.debugger.vm.registers[12] == 10


def test_handle_assign_negative_number_to_register(shell):
    shell.handle_command("r12 = -0xabc")

    assert shell.debugger.vm.registers[12] == -0xABC


def test_handle_assign_to_memory_location(shell):
    shell.debugger.vm.registers[9] = 1000

    shell.handle_command("@R9 = 4000")

    assert shell.debugger.vm.memory[1000] == 4000


def test_handle_assign_to_PC(shell):
    shell.handle_command("pc = 10")

    assert shell.debugger.vm.pc == 10


def test_handle_assign_to_symbol(shell, capsys):
    shell.handle_command("f_c = 10")

    assert capsys.readouterr().out == "Eval error: cannot assign to symbol.\n"
    assert "f_c" not in shell.debugger.symbol_table


def test_handle_assign_to_arithmetic_expression(shell, capsys):
    shell.handle_command("1 + 1 = 3")

    assert (
        capsys.readouterr().out
        == "Eval error: cannot assign to arithmetic expression.\n"
    )


def test_handle_assign_with_undefined_symbol(shell, capsys):
    shell.debugger.vm.registers[4] = 42

    shell.handle_command("r4 = whatever")

    assert shell.debugger.vm.registers[4] == 42
    assert capsys.readouterr().out == "Eval error: whatever is not defined.\n"


def test_handle_assign_register_to_symbol(shell):
    shell.handle_command("r7 = add")

    assert shell.debugger.vm.registers[7] == 4


def test_handle_assign_with_invalid_syntax(shell, capsys):
    shell.handle_command("@ = R5")

    assert capsys.readouterr().out == "Parse error: premature end of input.\n"


def test_handle_assign_with_explicit_command(shell):
    shell.handle_command("assign r7 add")

    assert shell.debugger.vm.registers[7] == 4


def test_handle_assign_with_too_many_args(shell, capsys):
    shell.handle_command("assign r1 r2 r3")

    assert capsys.readouterr().out == "assign takes two arguments.\n"


def test_handle_print_register(shell, capsys):
    shell.handle_command("print R1")

    assert capsys.readouterr().out == "0\n"


def test_handle_print_PC_ret(shell, capsys):
    shell.debugger.vm.registers[13] = 2
    shell.handle_command("print PC_ret")

    assert capsys.readouterr().out == "2 [<string>:5]\n"


def test_handle_print_PC_ret_with_explicit_format(shell, capsys):
    shell.debugger.vm.registers[13] = 2
    shell.handle_command("print :xd PC_ret")

    assert capsys.readouterr().out == "0x0002 = 2\n"


def test_handle_print_with_format_string(shell, capsys):
    shell.debugger.vm.registers[5] = 2
    shell.handle_command("print :bl r5")

    assert capsys.readouterr().out == "0b0000000000000010 [<string>:5]\n"


def test_handle_print_zero_register_with_char_format_string(shell, capsys):
    shell.handle_command("print :c R0")

    assert capsys.readouterr().out == "'\\x00'\n"


def test_handle_print_large_int_with_char_format_string(shell, capsys):
    shell.debugger.vm.registers[5] = 1000
    shell.handle_command("print :c R5")

    assert capsys.readouterr().out == "not an ASCII character\n"


def test_handle_print_unsigned_integer_with_signed_format_string(shell, capsys):
    shell.debugger.vm.registers[5] = 42
    shell.handle_command("print :s R5")

    assert capsys.readouterr().out == "not a signed integer\n"


def test_handle_print_with_restrictive_format_string(shell, capsys):
    shell.debugger.vm.registers[13] = 2
    shell.handle_command("print :o r13")

    assert capsys.readouterr().out == "0o00000002\n"


def test_handle_print_memory_expression(shell, capsys):
    shell.debugger.vm.registers[1] = 4
    shell.debugger.vm.memory[4] = 42

    shell.handle_command("print @r1")

    assert capsys.readouterr().out == "42 = '*'\n"


def test_handle_print_PC(shell, capsys):
    shell.debugger.vm.pc = 4

    shell.handle_command("print PC")

    assert capsys.readouterr().out == "4 [<string>:7]\n"


def test_handle_print_PC_with_nonsense_value(shell, capsys):
    shell.debugger.vm.pc = 300

    shell.handle_command("print pc")

    assert capsys.readouterr().out == "300\n"


def test_handle_print_int(shell, capsys):
    shell.handle_command("print 17")

    assert capsys.readouterr().out == "17\n"


def test_handle_print_arithmetic_expression(shell, capsys):
    shell.handle_command("print :x 21 * (1+1)")

    assert capsys.readouterr().out == "0x002a\n"


def test_handle_print_with_another_arithmetic_expression(shell, capsys):
    shell.debugger.vm.registers[1] = 60

    shell.handle_command("print :d r1-12")

    assert capsys.readouterr().out == "48\n"


def test_handle_print_with_multiple_arguments(shell, capsys):
    shell.debugger.vm.registers[1] = 5
    shell.debugger.vm.registers[2] = 7
    shell.handle_command("print :d r1, r2")

    assert capsys.readouterr().out == "R1 = 5\nR2 = 7\n"


def test_handle_print_symbol(shell, capsys):
    shell.handle_command("print add")

    assert capsys.readouterr().out == "4 [<string>:7]\n"


def test_handle_print_undefined_symbol(shell, capsys):
    shell.handle_command("print whatever")

    assert capsys.readouterr().out == "Eval error: whatever is not defined.\n"


def test_handle_print_invalid_register(shell, capsys):
    shell.handle_command("print R17")

    assert capsys.readouterr().out == "Parse error: R17 is not a valid register.\n"


def test_handle_print_with_division_by_zero(shell, capsys):
    shell.handle_command("print 10 / 0")

    assert capsys.readouterr().out == "Eval error: division by zero.\n"


def test_handle_print_with_nested_division_by_zero(shell, capsys):
    shell.handle_command("print @(10 / 0)")

    assert capsys.readouterr().out == "Eval error: division by zero.\n"


def test_handle_print_with_integer_literal_too_big(shell, capsys):
    shell.handle_command("print 100000")

    assert capsys.readouterr().out == "Eval error: integer literal exceeds 16 bits.\n"


def test_handle_print_with_overflow_from_multiplication(shell, capsys):
    shell.handle_command("print 30000*40")

    assert capsys.readouterr().out == "Eval error: overflow from *.\n"


def test_handle_print_with_integer_literal_too_small(shell, capsys):
    shell.handle_command("print -65000")

    assert capsys.readouterr().out == "Eval error: overflow from unary -.\n"


def test_handle_print_with_invalid_format(shell, capsys):
    shell.handle_command("print :y R1")

    assert capsys.readouterr().out == "Unknown format specifier `y`.\n"


def test_handle_print_undefined_symbol_in_memory_expression(shell, capsys):
    shell.handle_command("print @whatever")

    assert capsys.readouterr().out == "Eval error: whatever is not defined.\n"


def test_handle_print_case_sensitive_symbol(shell, capsys):
    shell.debugger.symbol_table["ADD"] = 10

    shell.handle_command("print ADD")

    assert capsys.readouterr().out == "10\n"


def test_handle_print_with_too_few_args(shell, capsys):
    shell.handle_command("print")

    assert capsys.readouterr().out == "print takes one or more arguments.\n"


def test_handle_print_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_print") as mock_handle_print:
        shell.handle_command("p @R7")
        assert mock_handle_print.call_count == 1

        args, kwargs = mock_handle_print.call_args
        assert len(args) == 1
        assert args[0] == "@R7"
        assert len(kwargs) == 0


def test_handle_help(shell, capsys):
    shell.handle_command("help")

    out = capsys.readouterr().out
    assert "Available commands" in out
    assert "Error:" not in out


def test_handle_help_with_one_arg(shell, capsys):
    shell.handle_command("help next")

    out = capsys.readouterr().out
    # Make sure it's not just printing the regular help message.
    assert "Available commands" not in out
    assert "next" in out
    assert "Execute the current line" in out


def test_handle_help_with_abbreviated_command_name(shell, capsys):
    shell.handle_command("help n")

    out = capsys.readouterr().out
    # Make sure it's not just printing the regular help message.
    assert "Available commands" not in out
    assert "next" in out
    assert "Execute the current line" in out


def test_handle_help_with_multiple_args(shell, capsys):
    shell.handle_command("help break next")

    out = capsys.readouterr().out
    # Make sure it's not just printing the regular help message.
    assert "Available commands" not in out
    assert "next" in out
    assert "Execute the current line" in out
    assert "break" in out


def test_handle_help_with_all_commands(shell, capsys):
    shell.handle_command(
        "help assign break clear continue execute help info list ll next off on print \
         restart goto step undo quit asm dis"
    )

    assert "not a recognized command" not in capsys.readouterr().out


def test_handle_help_with_unknown_command(shell, capsys):
    shell.handle_command("help whatever")

    assert capsys.readouterr().out == "whatever is not a recognized command.\n"


def test_handle_help_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_help") as mock_handle_help:
        shell.handle_command("h break")
        assert mock_handle_help.call_count == 1

        args, kwargs = mock_handle_help.call_args
        assert len(args) == 1
        assert args[0] == ["break"]
        assert len(kwargs) == 0


def test_handle_step(capsys):
    shell = load_shell(
        """\
SET(R1, 4)
CALL(FP_alt, plus_two)
SET(R2, 5)
HALT()

LABEL(plus_two)
  INC(R1, 2)
  RETURN(FP_alt, PC_ret)
"""
    )
    shell.handle_command("n")
    capsys.readouterr()
    shell.handle_command("step")

    assert shell.debugger.vm.pc == 8
    assert shell.debugger.vm.registers[1] == 4
    assert shell.debugger.vm.registers[2] == 0

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>]

    6  LABEL(plus_two)
->  7    INC(R1, 2)
    8    RETURN(FP_alt, PC_ret)
"""
    )


def test_handle_step_not_on_CALL(shell, capsys):
    shell.handle_command("step")

    assert (
        capsys.readouterr().out
        == "step is only valid when the current instruction is CALL.\n"
    )


def test_handle_step_with_too_many_args(shell, capsys):
    shell.handle_command("step 1")

    assert capsys.readouterr().out == "step takes no arguments.\n"


def test_handle_step_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_step") as mock_handle_step:
        shell.handle_command("s")
        assert mock_handle_step.call_count == 1


def test_handle_undo_after_next(shell, capsys):
    shell.handle_command("n")
    capsys.readouterr()
    shell.handle_command("undo")

    assert capsys.readouterr().out == "Undid next.\n"
    assert shell.debugger.vm.pc == 0
    assert shell.debugger.vm.registers[1] == 0


def test_handle_undo_after_next_and_print(shell, capsys):
    shell.handle_command("n")
    shell.handle_command("p r1")
    capsys.readouterr()
    shell.handle_command("undo")

    assert capsys.readouterr().out == "Undid next.\n"
    assert shell.debugger.vm.pc == 0
    assert shell.debugger.vm.registers[1] == 0


def test_handle_undo_after_break_and_continue(shell, capsys):
    shell.handle_command("b add")
    shell.handle_command("continue")
    capsys.readouterr()
    shell.handle_command("undo")
    shell.handle_command("undo")

    assert capsys.readouterr().out == "Undid continue.\nUndid break.\n"
    assert shell.debugger.vm.pc == 0
    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert len(shell.debugger.breakpoints) == 0


def test_handle_undo_after_print(shell, capsys):
    shell.handle_command("print r1")
    capsys.readouterr()
    shell.handle_command("undo")

    assert capsys.readouterr().out == "Nothing to undo.\n"


def test_handle_undo_after_nothing(shell, capsys):
    shell.handle_command("undo")

    assert capsys.readouterr().out == "Nothing to undo.\n"


def test_handle_undo_after_assign(shell, capsys):
    shell.handle_command("r1 = 666")
    shell.handle_command("undo")

    assert shell.debugger.vm.registers[1] == 0
    assert capsys.readouterr().out == "Undid assign.\n"


def test_handle_undo_after_clear(shell, capsys):
    shell.handle_command("break 4")
    shell.handle_command("clear *")
    capsys.readouterr()

    shell.handle_command("undo")

    assert len(shell.debugger.breakpoints) == 1
    assert capsys.readouterr().out == "Undid clear.\n"


def test_handle_undo_twice(shell, capsys):
    shell.handle_command("n")
    shell.handle_command("n")
    capsys.readouterr()
    shell.handle_command("undo")
    shell.handle_command("undo")

    assert capsys.readouterr().out == "Undid next.\nUndid next.\n"
    assert shell.debugger.vm.pc == 0
    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0


def test_handle_undo_with_too_many_args(shell, capsys):
    shell.handle_command("undo 1")

    assert capsys.readouterr().out == "undo takes no arguments.\n"


def test_handle_undo_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_undo") as mock_handle_undo:
        shell.handle_command("u")
        assert mock_handle_undo.call_count == 1


def test_handle_dis(shell, capsys):
    shell.handle_command("dis 0xe1ff")

    assert capsys.readouterr().out == "SETLO(R1, 255)\n"


def test_handle_dis_with_multiple_arguments(shell, capsys):
    shell.handle_command("dis 0xe198 0xf1b7")

    assert capsys.readouterr().out == "SETLO(R1, 152)\nSETHI(R1, 183)\n"


def test_handle_dis_invalid_argument(shell, capsys):
    shell.handle_command("dis abc")

    assert capsys.readouterr().out == "Could not parse argument `abc` to dis.\n"


def test_handle_dis_with_an_OPCODE(capsys):
    shell = load_shell("OPCODE(0x3132)")
    shell.handle_command("dis")

    assert capsys.readouterr().out == "LSR8(R1, R2)\n"


def test_handle_dis_without_an_OPCODE(shell, capsys):
    shell.handle_command("dis")

    assert capsys.readouterr().out == "Current operation is not an OPCODE.\n"

    # Make sure it doesn't choke at the end of program.
    shell.handle_command("continue")
    capsys.readouterr()
    shell.handle_command("dis")

    assert capsys.readouterr().out == "Current operation is not an OPCODE.\n"


def test_handle_asm(shell, capsys):
    shell.handle_command("asm SETLO(R1, 255)")

    assert capsys.readouterr().out == "e1ff\n"


def test_handle_asm_with_only_data(shell, capsys):
    shell.handle_command("asm INTEGER(42)")

    assert capsys.readouterr().out == "49152*0\nc002\n2a\n"


def test_handle_asm_with_data_and_code(shell, capsys):
    shell.handle_command("asm DLABEL(x) INTEGER(42) SET(R1, x)")

    assert (
        capsys.readouterr().out
        == """\
[DATA]
  49152*0
  c002
  2a
[CODE]
  e101
  f1c0
"""
    )


def test_handle_asm_with_too_few_args(shell, capsys):
    shell.handle_command("asm")

    assert capsys.readouterr().out == "asm takes one argument.\n"


def test_handle_unknown_command(shell, capsys):
    shell.handle_command("whatever")

    assert capsys.readouterr().out == "whatever is not a recognized command.\n"


def test_handle_unknown_command_with_arg(shell, capsys):
    shell.handle_command("run program")

    assert capsys.readouterr().out == "run is not a recognized command.\n"


def test_handle_attempt_to_print_register(shell, capsys):
    shell.handle_command("r1")

    assert capsys.readouterr().out == "r1 is not a recognized command.\n"


def test_data_statements(capsys):
    shell = load_shell("DLABEL(X)\nINTEGER(42)\nSET(R1, X)")

    assert shell.debugger.vm.load_memory(DEFAULT_DATA_START) == 42


def test_resolve_location_with_line_number(debugger):
    assert debugger.resolve_location("4") == 0


def test_resolve_location_with_label(debugger):
    assert debugger.resolve_location("add") == 4


def test_resolve_location_fails_with_constant(debugger):
    with pytest.raises(ValueError) as e:
        debugger.resolve_location("N")
    assert "could not locate label `N`" in str(e)


def test_resolve_location_out_of_range(debugger):
    with pytest.raises(ValueError) as e:
        debugger.resolve_location("100")
    assert "could not find corresponding line" in str(e)


def test_resolve_location_invalid_format(debugger):
    with pytest.raises(ValueError) as e:
        debugger.resolve_location("a")
    assert "could not locate label `a`" in str(e)


def test_get_breakpoint_name(debugger):
    # Zero'th instruction corresponds to second line.
    assert debugger.get_breakpoint_name(0) == "<string>:4"


def test_get_breakpoint_name_with_label(debugger):
    assert debugger.get_breakpoint_name(4) == "<string>:7 (add)"


def test_get_breakpoint_name_does_not_include_constant(debugger):
    assert debugger.get_breakpoint_name(3) == "<string>:5"


def test_print_current_op(shell, capsys):
    shell.print_current_op()

    captured = capsys.readouterr()
    assert (
        captured.out
        == """\
[<string>]

    3
->  4  SET(R1, N)
    5  SET(R2, 39)
"""
    )


def test_reverse_lookup_label():
    symbol_table = {"n": Constant(11), "end": Label(11)}
    assert reverse_lookup_label(symbol_table, 11) == "end"
    assert reverse_lookup_label(symbol_table, 12) is None


def test_debug_empty_program(capsys):
    debug(Program([], [], {}, None), Settings())

    assert capsys.readouterr().out == "Cannot debug an empty program.\n"


def test_label_on_last_line(capsys):
    shell = load_shell("NOP()\nLABEL(my_label)")
    shell.handle_command("info sym")

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "my_label" in captured.out
