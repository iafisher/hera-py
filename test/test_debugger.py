import pytest
from unittest.mock import patch

from hera.data import Constant, Label, Op, State
from hera.debugger import debug, Debugger, Shell
from hera.debugger.debugger import reverse_lookup_label
from hera.loader import load_program, load_program_from_file


@pytest.fixture
def shell():
    return Shell(Debugger(SAMPLE_PROGRAM, SYMBOL_TABLE))


@pytest.fixture
def debugger():
    return Debugger(SAMPLE_PROGRAM, SYMBOL_TABLE)


def load_shell(program):
    return Shell(Debugger(*load_program(program, State())))


SAMPLE_PROGRAM, SYMBOL_TABLE = load_program(
    """\
// A comment
CONSTANT(N, 3)

SET(R1, N)
SET(R2, 39)
LABEL(add)
ADD(R3, R1, R2)
HALT()
""",
    State(),
)


def test_handle_break_prints_breakpoints(shell, capsys):
    shell.debugger.breakpoints[4] = "main.hera:7"
    shell.handle_command("break")

    assert capsys.readouterr().out == "main.hera:7\n"


def test_handle_break_prints_breakpoints_with_no_breakpoints_set(shell, capsys):
    shell.handle_command("break")

    assert capsys.readouterr().out == "No breakpoints set.\n"


def test_handle_break_sets_breakpoint(shell):
    assert len(shell.debugger.breakpoints) == 0

    shell.handle_command("break 4")

    assert len(shell.debugger.breakpoints) == 1
    assert 0 in shell.debugger.breakpoints
    assert shell.debugger.breakpoints[0] == "<string>:4"


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


def test_handle_next(shell):
    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.pc == 0

    shell.handle_command("next")

    assert shell.debugger.vm.registers[1] == 3
    assert shell.debugger.vm.pc == 2


def test_handle_next_with_HALT(shell, capsys):
    # Last instruction of SAMPLE_PROGRAM is a HALT operation.
    shell.debugger.vm.pc = 5

    shell.handle_command("next")

    assert shell.debugger.vm.pc == 5
    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_handle_next_after_end_of_program(shell, capsys):
    shell.debugger.vm.pc = 9000

    shell.handle_command("next")

    assert shell.debugger.vm.pc == 9000
    assert (
        capsys.readouterr().out
        == "Program has finished executing. Enter 'r' to restart.\n"
    )


def test_handle_next_with_too_many_args(shell, capsys):
    # TODO: It would actually be useful if this worked.
    shell.handle_command("next 10")

    assert capsys.readouterr().out == "next takes no arguments.\n"


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


def test_handle_skip_with_increment(shell):
    shell.handle_command("skip +2")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 4


def test_handle_skip_with_no_arg(shell):
    shell.handle_command("skip")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 2


def test_handle_skip_with_line_number(shell):
    shell.handle_command("skip 7")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 4


@pytest.mark.skip("Should this work?")
def test_handle_skip_with_line_number_not_on_operation(shell):
    # A line number that doesn't correspond to an actual operation.
    shell.handle_command("skip 6")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 4


def test_handle_skip_with_label(shell):
    shell.handle_command("skip add")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 4


def test_handle_skip_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_skip") as mock_handle_skip:
        shell.handle_command("sk 10")
        assert mock_handle_skip.call_count == 1

        args, kwargs = mock_handle_skip.call_args
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

Constants: N (3)
Labels: add (<string>:7)
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

Constants: N (3)
Labels: add (<string>:7)
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

Constants: N (3)
Labels: add (<string>:7)
"""
    )


def test_handle_info_with_too_many_args(shell, capsys):
    shell.handle_command("info 1")

    assert capsys.readouterr().out == "info takes no arguments.\n"


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


def test_handle_list_with_too_many_args(shell, capsys):
    shell.handle_command("list 1 2")

    assert capsys.readouterr().out == "list takes zero or one arguments.\n"


def test_get_previous_ops(debugger):
    debugger.vm.pc = 4
    previous_three = debugger.get_previous_ops(3)

    assert len(previous_three) == 2
    assert previous_three[0][1].name == "SET"
    assert previous_three[0][1].args[0] == "R1"
    assert previous_three[1][1].name == "SET"
    assert previous_three[1][1].args[0] == "R2"


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
"""
    )


def test_handle_ll_with_too_many_args(shell, capsys):
    shell.handle_command("ll 1")

    assert capsys.readouterr().out == "ll takes no arguments.\n"


def test_handle_abbreviated_ll(shell, capsys):
    with patch("hera.debugger.shell.Shell.handle_ll") as mock_handle_ll:
        shell.handle_command("ll")
        assert mock_handle_ll.call_count == 1


def test_handle_assign_to_register(shell):
    shell.handle_command("r12 = 10")

    assert shell.debugger.vm.registers[12] == 10


def test_handle_assign_to_memory_location(shell):
    shell.debugger.vm.registers[9] = 1000

    shell.handle_command("m[R9] = 4000")

    assert shell.debugger.vm.memory[1000] == 4000


def test_handle_assign_to_PC(shell):
    shell.handle_command("pc = 10")

    assert shell.debugger.vm.pc == 10


def test_handle_assign_to_flag(shell):
    shell.handle_command("f_c = #t")

    assert shell.debugger.vm.flag_carry


def test_handle_assign_to_symbol(shell, capsys):
    shell.handle_command("foo = 10")

    assert capsys.readouterr().out == "Eval error: cannot assign to symbol.\n"
    assert "foo" not in shell.debugger.symbol_table


def test_handle_assign_non_boolean_to_flag(shell, capsys):
    shell.handle_command("f_c = 10")

    assert (
        capsys.readouterr().out
        == "Eval error: cannot assign non-boolean value to flag (use #t and #f instead).\n"
    )


def test_handle_assign_with_undefined_symbol(shell, capsys):
    shell.debugger.vm.registers[4] = 42

    shell.handle_command("r4 = whatever")

    assert shell.debugger.vm.registers[4] == 42
    assert capsys.readouterr().out == "Eval error: undefined symbol `whatever`.\n"


def test_handle_assign_register_to_symbol(shell):
    shell.handle_command("r7 = add")

    assert shell.debugger.vm.registers[7] == 4


def test_handle_assign_with_explicit_command(shell):
    shell.handle_command("assign r7 add")

    assert shell.debugger.vm.registers[7] == 4


def test_handle_print_register(shell, capsys):
    shell.handle_command("print R1")

    assert capsys.readouterr().out == "R1 = 0x0000 = 0\n"


def test_handle_print_memory_expression(shell, capsys):
    shell.debugger.vm.registers[1] = 4
    shell.debugger.vm.memory[4] = 42

    shell.handle_command("print M[r1]")

    assert capsys.readouterr().out == "M[4] = 42\n"


def test_handle_print_PC(shell, capsys):
    shell.debugger.vm.pc = 3

    shell.handle_command("print pc")

    assert capsys.readouterr().out == "PC = 3\n"


def test_handle_print_symbol(shell, capsys):
    shell.handle_command("print add")

    assert capsys.readouterr().out == "add = 4 (label)\n"


def test_handle_print_flag(shell, capsys):
    shell.handle_command("print f_cb")
    shell.handle_command("print f_c")
    shell.handle_command("print f_v")
    shell.handle_command("print f_s")
    shell.handle_command("print f_z")

    assert (
        capsys.readouterr().out
        == """\
Carry-block flag = false
Carry flag = false
Overflow flag = false
Sign flag = false
Zero flag = false
"""
    )


def test_handle_print_flag_with_conflicting_symbol(shell, capsys):
    shell.debugger.symbol_table["f_cb"] = 42
    shell.handle_command("print f_cb")

    assert capsys.readouterr().out == "Carry-block flag = false\nf_cb = 42\n"


def test_handle_print_case_sensitive_symbol(shell, capsys):
    shell.debugger.symbol_table["ADD"] = 10

    shell.handle_command("print ADD")

    assert capsys.readouterr().out == "ADD = 10\n"


def test_handle_print_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_print") as mock_handle_print:
        shell.handle_command("p M[ R7 ]")
        assert mock_handle_print.call_count == 1

        args, kwargs = mock_handle_print.call_args
        assert len(args) == 1
        assert args[0] == "M[ R7 ]"
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
        "help assign break continue execute help info list ll next print restart skip \
         step quit"
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

    assert shell.debugger.vm.pc == 5
    assert shell.debugger.vm.registers[1] == 6
    assert shell.debugger.vm.registers[2] == 0

    captured = capsys.readouterr().out
    assert captured == "3  SET(R2, 5)\n"


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
        shell.handle_command("st")
        assert mock_handle_step.call_count == 1


def test_handle_command_s(shell, capsys):
    shell.handle_command("s")

    assert capsys.readouterr().out == "s is ambiguous between skip and step.\n"


def test_handle_unknown_command(shell, capsys):
    shell.handle_command("whatever")

    assert capsys.readouterr().out == "whatever is not a recognized command.\n"


def test_handle_unknown_command_with_arg(shell, capsys):
    shell.handle_command("run program")

    assert capsys.readouterr().out == "run is not a recognized command.\n"


def test_handle_attempt_to_print_register(shell, capsys):
    shell.handle_command("r1")

    assert capsys.readouterr().out == "r1 is not a recognized command.\n"


def test_resolve_location_with_line_number(debugger):
    assert debugger.resolve_location(4) == 0


def test_resolve_location_with_label(debugger):
    assert debugger.resolve_location("add") == 4


def test_resolve_location_fails_with_constant(debugger):
    with pytest.raises(ValueError) as e:
        debugger.resolve_location("N")
    assert "could not locate label `N`" in str(e)


def test_resolve_location_out_of_range(debugger):
    with pytest.raises(ValueError) as e:
        debugger.resolve_location(100)
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
    assert captured.out == "4  SET(R1, N)\n"


def test_reverse_lookup_label():
    symbol_table = {"n": Constant(11), "end": Label(11)}
    assert reverse_lookup_label(symbol_table, 11) == "end"
    assert reverse_lookup_label(symbol_table, 12) == None


def test_debug_empty_program(capsys):
    debug([], {})

    assert capsys.readouterr().out == "Cannot debug an empty program.\n"
