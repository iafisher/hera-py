import pytest
from unittest.mock import patch

from hera.data import Op
from hera.debugger import debug, Debugger, reverse_lookup_label
from hera.loader import load_program, load_program_from_file
from hera.typechecker import Constant, Label


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


def test_print_breakpoints(debugger, capsys):
    debugger.breakpoints[4] = "main.hera:7"
    debugger.handle_command("break")

    assert capsys.readouterr().out == "main.hera:7\n"


def test_print_breakpoints_with_no_breakpoints_set(debugger, capsys):
    debugger.handle_command("break")

    assert capsys.readouterr().out == "No breakpoints set.\n"


def test_set_breakpoint(debugger):
    assert len(debugger.breakpoints) == 0

    debugger.handle_command("break 4")

    assert len(debugger.breakpoints) == 1
    assert 0 in debugger.breakpoints
    assert debugger.breakpoints[0] == "<string>:4"


def test_set_breakpoint_not_on_line_of_code(debugger, capsys):
    debugger.handle_command("break 1")

    assert len(debugger.breakpoints) == 0
    assert capsys.readouterr().out == "Error: could not find corresponding line.\n"


def test_set_unparseable_breakpoint(debugger, capsys):
    debugger.handle_command("break $$$")

    assert len(debugger.breakpoints) == 0
    assert capsys.readouterr().out == "Error: could not locate label `$$$`.\n"


def test_execute_break_with_too_many_args(debugger, capsys):
    debugger.handle_command("break 1 2 3")

    assert len(debugger.breakpoints) == 0
    assert capsys.readouterr().out == "break takes zero or one arguments.\n"


def test_execute_abbreviated_break(debugger):
    with patch("hera.debugger.Debugger.exec_break") as mock_exec_break:
        debugger.handle_command("b 7")
        assert mock_exec_break.call_count == 1

        args, kwargs = mock_exec_break.call_args
        assert len(args) == 1
        assert args[0] == ["7"]
        assert len(kwargs) == 0


def test_execute_next(debugger):
    assert debugger.vm.registers[1] == 0
    assert debugger.vm.pc == 0

    debugger.handle_command("next")

    assert debugger.vm.registers[1] == 3
    assert debugger.vm.pc == 2


def test_execute_next_with_halt(debugger, capsys):
    # Last instruction of SAMPLE_PROGRAM is a HALT operation.
    debugger.vm.pc = 5

    debugger.handle_command("next")

    assert debugger.vm.pc == 5
    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_execute_next_after_end_of_program(debugger, capsys):
    debugger.vm.pc = 9000

    debugger.handle_command("next")

    assert debugger.vm.pc == 9000
    assert (
        capsys.readouterr().out
        == "Program has finished executing. Press 'r' to restart.\n"
    )


def test_execute_next_with_too_many_args(debugger, capsys):
    # TODO: It would actually be useful if this worked.
    debugger.handle_command("next 10")

    assert capsys.readouterr().out == "next takes no arguments.\n"


def test_execute_abbreviated_next(debugger):
    with patch("hera.debugger.Debugger.exec_next") as mock_exec_next:
        debugger.handle_command("n")
        assert mock_exec_next.call_count == 1


def test_execute_continue_with_breakpoint(debugger):
    debugger.breakpoints[4] = ""

    debugger.handle_command("continue")

    assert debugger.vm.registers[1] == 3
    assert debugger.vm.registers[2] == 39
    assert debugger.vm.registers[3] == 0
    assert debugger.vm.pc == 4

    # Make sure continuing again doesn't loop on the same instruction.
    debugger.handle_command("continue")
    assert debugger.vm.pc == 5


def test_execute_continue_without_breakpoint(debugger, capsys):
    debugger.handle_command("continue")

    assert debugger.vm.registers[1] == 3
    assert debugger.vm.registers[2] == 39
    assert debugger.vm.registers[3] == 42
    assert debugger.vm.pc == 5
    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_execute_continue_with_too_many_args(debugger, capsys):
    debugger.handle_command("continue 10")

    assert capsys.readouterr().out == "continue takes no arguments.\n"


def test_execute_abbreviated_continue(debugger):
    with patch("hera.debugger.Debugger.exec_continue") as mock_exec_continue:
        debugger.handle_command("c")
        assert mock_exec_continue.call_count == 1


def test_print_register(debugger, capsys):
    debugger.vm.registers[7] = 42

    debugger.handle_command("print r7")

    assert capsys.readouterr().out == "r7 = 0x002a = 42 = '*'\n"


def test_print_invalid_register(debugger, capsys):
    debugger.handle_command("print r17")

    assert capsys.readouterr().out == "Could not parse argument to print.\n"


def test_print_program_counter(debugger, capsys):
    debugger.vm.pc = 7

    debugger.handle_command("print PC")

    assert capsys.readouterr().out == "PC = 7\n"


def test_print_memory_location(debugger, capsys):
    debugger.vm.assign_memory(97, 1000)

    debugger.handle_command("print m[97]")

    assert capsys.readouterr().out == "M[97] = 1000\n"


def test_print_hex_memory_location(debugger, capsys):
    debugger.vm.assign_memory(0xAB, 1000)

    debugger.handle_command("print m[0xaB]")

    assert capsys.readouterr().out == "M[171] = 1000\n"


def test_print_memory_location_from_register(debugger, capsys):
    debugger.vm.registers[5] = 0xAB
    debugger.vm.assign_memory(0xAB, 1000)

    debugger.handle_command("print m[r5]")

    assert capsys.readouterr().out == "M[171] = 1000\n"


def test_print_invalid_memory_location(debugger, capsys):
    debugger.handle_command("print m[???]")

    assert capsys.readouterr().out == "Could not parse memory location.\n"


def test_print_constant(debugger, capsys):
    debugger.handle_command("print N")

    assert capsys.readouterr().out == "N = 3\n"


def test_execute_print_with_too_few_args(debugger, capsys):
    # TODO: It would be useful if this printed the last printed expression again.
    debugger.handle_command("print")

    assert capsys.readouterr().out == "print takes one argument.\n"


def test_execute_abbreviated_print(debugger):
    with patch("hera.debugger.Debugger.exec_print") as mock_exec_print:
        debugger.handle_command("p r7")
        assert mock_exec_print.call_count == 1

        args, kwargs = mock_exec_print.call_args
        assert len(args) == 1
        assert args[0] == ["r7"]
        assert len(kwargs) == 0


def test_execute_skip(debugger):
    debugger.handle_command("skip 2")

    assert debugger.vm.pc == 4


def test_execute_skip_with_no_arg(debugger):
    debugger.handle_command("skip")

    assert debugger.vm.pc == 2


def test_execute_abbreviated_skip(debugger):
    with patch("hera.debugger.Debugger.exec_skip") as mock_exec_skip:
        debugger.handle_command("s 10")
        assert mock_exec_skip.call_count == 1

        args, kwargs = mock_exec_skip.call_args
        assert len(args) == 1
        assert args[0] == ["10"]
        assert len(kwargs) == 0


def test_execute_list(debugger, capsys):
    debugger.handle_command("list")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>, lines 4-8]

-> 0000  SET(R1, 3)
   0002  SET(R2, 39)
   0004  ADD(R3, R1, R2)
   0005  HALT()
"""
    )


def test_execute_list_middle_of_program(debugger, capsys):
    debugger.vm.pc = 4
    debugger.handle_command("list")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>, lines 4-8]

   0000  SET(R1, 3)
   0002  SET(R2, 39)
-> 0004  ADD(R3, R1, R2)
   0005  HALT()
"""
    )


def test_execute_list_with_context_arg(debugger, capsys):
    debugger.vm.pc = 2
    debugger.handle_command("list 1")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[<string>, lines 4-7]

   0000  SET(R1, 3)
-> 0002  SET(R2, 39)
   0004  ADD(R3, R1, R2)
"""
    )


def test_execute_list_with_invalid_context_arg(debugger, capsys):
    debugger.handle_command("list abc")

    assert capsys.readouterr().out == "Could not parse argument to list.\n"


def test_execute_list_with_too_many_args(debugger, capsys):
    debugger.handle_command("list 1 2")

    assert capsys.readouterr().out == "list takes zero or one arguments.\n"


def test_get_previous_ops(debugger):
    debugger.vm.pc = 4
    previous_three = debugger.get_previous_ops(3)

    assert len(previous_three) == 2
    assert previous_three[0][1].name == "SET"
    assert previous_three[0][1].args[0] == "R1"
    assert previous_three[1][1].name == "SET"
    assert previous_three[1][1].args[0] == "R2"


def test_execute_abbreviated_list(debugger):
    with patch("hera.debugger.Debugger.exec_list") as mock_exec_list:
        debugger.handle_command("l")
        assert mock_exec_list.call_count == 1


def test_execute_long_list(debugger, capsys):
    debugger.handle_command("longlist")

    captured = capsys.readouterr().out
    assert (
        captured
        == """\
-> 0000  SET(R1, 3)
   0002  SET(R2, 39)
   0004  ADD(R3, R1, R2)
   0005  HALT()
"""
    )


def test_execute_long_list_with_too_many_args(debugger, capsys):
    debugger.handle_command("longlist 1")

    assert capsys.readouterr().out == "longlist takes no arguments.\n"


def test_execute_abbreviated_long_list(debugger, capsys):
    with patch("hera.debugger.Debugger.exec_long_list") as mock_exec_long_list:
        debugger.handle_command("ll")
        assert mock_exec_long_list.call_count == 1


def test_execute_help(debugger, capsys):
    debugger.handle_command("help")

    out = capsys.readouterr().out
    assert "Available commands" in out
    assert "Error:" not in out


def test_execute_unknown_command(debugger, capsys):
    debugger.handle_command("whatever")

    assert capsys.readouterr().out == "whatever is not a known command.\n"


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


def test_print_current_op(debugger, capsys):
    debugger.print_current_op()

    captured = capsys.readouterr()
    assert captured.out == "[<string>, line 4]\n\n0000  SET(R1, 3)\n"


def test_reverse_lookup_label():
    symbol_table = {"n": Constant(11), "end": Label(11)}
    assert reverse_lookup_label(symbol_table, 11) == "end"
    assert reverse_lookup_label(symbol_table, 12) == None


def test_debug_empty_program(capsys):
    debug([], {})

    assert capsys.readouterr().out == "Cannot debug an empty program.\n"
