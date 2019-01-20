import pytest
from unittest.mock import patch

from hera.data import Op
from hera.debugger import debug, Debugger, Shell
from hera.debugger.debugger import reverse_lookup_label
from hera.loader import load_program, load_program_from_file
from hera.typechecker import Constant, Label


@pytest.fixture
def shell():
    return Shell(Debugger(SAMPLE_PROGRAM, SYMBOL_TABLE))


@pytest.fixture
def debugger():
    return Debugger(SAMPLE_PROGRAM, SYMBOL_TABLE)


SAMPLE_PROGRAM, SYMBOL_TABLE = load_program(
    """\
// A comment
CONSTANT(N, 3)

SET(R1, N)
SET(R2, 39)
LABEL(add)
ADD(R3, R1, R2)
HALT()
"""
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


@pytest.mark.skip("Going to be hard to implement this")
def test_handle_execute_with_label(shell, capsys):
    shell.handle_command("execute LABEL(l)")

    assert shell.debugger.vm.pc == 0
    assert capsys.readouterr().out == "execute cannot take labels.\n"


def test_handle_skip(shell):
    shell.handle_command("skip 2")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 4


def test_handle_skip_with_no_arg(shell):
    shell.handle_command("skip")

    assert shell.debugger.vm.registers[1] == 0
    assert shell.debugger.vm.registers[2] == 0
    assert shell.debugger.vm.pc == 2


def test_handle_skip_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_skip") as mock_handle_skip:
        shell.handle_command("s 10")
        assert mock_handle_skip.call_count == 1

        args, kwargs = mock_handle_skip.call_args
        assert len(args) == 1
        assert args[0] == ["10"]
        assert len(kwargs) == 0


def test_handle_list(shell, capsys):
    shell.handle_command("list")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>, lines 4-8]

-> 0000  SET(R1, 3)
   0002  SET(R2, 39)
   0004  ADD(R3, R1, R2) [add]
   0005  HALT()
"""
    )


def test_handle_list_in_middle_of_program(shell, capsys):
    shell.debugger.vm.pc = 4
    shell.handle_command("list")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>, lines 4-8]

   0000  SET(R1, 3)
   0002  SET(R2, 39)
-> 0004  ADD(R3, R1, R2) [add]
   0005  HALT()
"""
    )


def test_handle_list_with_context_arg(shell, capsys):
    shell.debugger.vm.pc = 2
    shell.handle_command("list 1")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>, lines 4-7]

   0000  SET(R1, 3)
-> 0002  SET(R2, 39)
   0004  ADD(R3, R1, R2) [add]
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


def test_handle_long_list(shell, capsys):
    shell.handle_command("longlist")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
-> 0000  SET(R1, 3)
   0002  SET(R2, 39)
   0004  ADD(R3, R1, R2) [add]
   0005  HALT()
"""
    )


def test_handle_long_list_with_multiple_labels_on_same_line(shell, capsys):
    shell.debugger.reverse_labels[4].append("another_one")

    shell.handle_command("longlist")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
-> 0000  SET(R1, 3)
   0002  SET(R2, 39)
   0004  ADD(R3, R1, R2) [add, another_one]
   0005  HALT()
"""
    )


def test_handle_long_list_with_too_many_args(shell, capsys):
    shell.handle_command("longlist 1")

    assert capsys.readouterr().out == "longlist takes no arguments.\n"


def test_handle_abbreviated_long_list(shell, capsys):
    with patch("hera.debugger.shell.Shell.handle_long_list") as mock_handle_long_list:
        shell.handle_command("ll")
        assert mock_handle_long_list.call_count == 1


def test_handle_rr(shell, capsys):
    shell.handle_command("rr")

    assert capsys.readouterr().out == "All registers are set to zero.\n"


def test_handle_rr_with_real_values(shell, capsys):
    shell.debugger.vm.registers[3] = 11
    shell.debugger.vm.registers[7] = 42

    shell.handle_command("rr")

    assert (
        capsys.readouterr().out
        == """\
R1 = 0x0000 = 0
R2 = 0x0000 = 0
R3 = 0x000b = 11
R4 = 0x0000 = 0
R5 = 0x0000 = 0
R6 = 0x0000 = 0
R7 = 0x002a = 42 = '*'

All higher registers are set to zero.
"""
    )


def test_handle_rr_with_all_registers_set(shell, capsys):
    shell.debugger.vm.registers[15] = 42

    shell.handle_command("rr")

    assert (
        capsys.readouterr().out
        == """\
R1 = 0x0000 = 0
R2 = 0x0000 = 0
R3 = 0x0000 = 0
R4 = 0x0000 = 0
R5 = 0x0000 = 0
R6 = 0x0000 = 0
R7 = 0x0000 = 0
R8 = 0x0000 = 0
R9 = 0x0000 = 0
R10 = 0x0000 = 0
R11 = 0x0000 = 0
R12 = 0x0000 = 0
R13 = 0x0000 = 0
R14 = 0x0000 = 0
R15 = 0x002a = 42 = '*'
"""
    )


def test_handle_symbols(shell, capsys):
    shell.handle_command("symbols")

    assert capsys.readouterr().out == "add = 4 (label)\nN = 3 (constant)\n"


def test_handle_symbols_with_too_many_args(shell, capsys):
    shell.handle_command("symbols a")

    assert capsys.readouterr().out == "symbols takes no arguments.\n"


def test_handle_symbols_abbreviated(shell):
    with patch("hera.debugger.shell.Shell.handle_symbols") as mock_handle_symbols:
        shell.handle_command("sym")
        assert mock_handle_symbols.call_count == 1


def test_handle_register_expression(shell, capsys):
    shell.handle_command("R1")

    assert capsys.readouterr().out == "R1 = 0x0000 = 0\n"


def test_handle_memory_expression(shell, capsys):
    shell.debugger.vm.registers[1] = 4
    shell.debugger.vm.memory[4] = 42

    shell.handle_command("M[r1]")

    assert capsys.readouterr().out == "M[4] = 42\n"


def test_handle_setting_a_register(shell):
    shell.handle_command("r12 = 10")

    assert shell.debugger.vm.registers[12] == 10


def test_handle_setting_a_memory_location(shell):
    shell.debugger.vm.registers[9] = 1000

    shell.handle_command("m[R9] = 4000")

    assert shell.debugger.vm.memory[1000] == 4000


def test_handle_pc(shell, capsys):
    shell.debugger.vm.pc = 3

    shell.handle_command("pc")

    assert capsys.readouterr().out == "PC = 3\n"


def test_handle_setting_pc(shell):
    shell.handle_command("pc = 10")

    assert shell.debugger.vm.pc == 10


def test_handle_symbol(shell, capsys):
    shell.handle_command("add")

    assert capsys.readouterr().out == "add = 4 (label)\n"


def test_handle_undefined_symbol(shell, capsys):
    shell.debugger.vm.registers[4] = 42

    shell.handle_command("r4 = whatever")

    assert shell.debugger.vm.registers[4] == 42
    assert capsys.readouterr().out == "Eval error: undefined symbol `whatever`.\n"


def test_handle_case_sensitive_symbol(shell, capsys):
    shell.debugger.symbol_table["ADD"] = 10

    shell.handle_command("ADD")

    assert capsys.readouterr().out == "ADD = 10\n"


def test_handle_setting_register_to_symbol(shell):
    shell.handle_command("r7 = add")

    assert shell.debugger.vm.registers[7] == 4


def test_handle_help(shell, capsys):
    shell.handle_command("help")

    out = capsys.readouterr().out
    assert "Available commands" in out
    assert "Error:" not in out


def test_handle_unknown_command(shell, capsys):
    shell.handle_command("whatever")

    assert (
        capsys.readouterr().out == "whatever is not a recognized command or symbol.\n"
    )


def test_handle_unknown_command_with_arg(shell, capsys):
    shell.handle_command("run program")

    assert capsys.readouterr().out == "run is not a recognized command or symbol.\n"


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
    assert captured.out == "[<string>, line 4]\n\n0000  SET(R1, 3)\n"


def test_reverse_lookup_label():
    symbol_table = {"n": Constant(11), "end": Label(11)}
    assert reverse_lookup_label(symbol_table, 11) == "end"
    assert reverse_lookup_label(symbol_table, 12) == None


def test_debug_empty_program(capsys):
    debug([], {})

    assert capsys.readouterr().out == "Cannot debug an empty program.\n"
