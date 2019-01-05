import pytest
from unittest.mock import patch

from hera.debugger import Debugger
from hera.loader import load_program_from_file


@pytest.fixture
def debugger():
    return Debugger(SAMPLE_PROGRAM, SYMBOL_TABLE)


SAMPLE_PROGRAM, SYMBOL_TABLE = load_program_from_file("test/assets/unit/debugger.hera")


def test_print_breakpoints(debugger, capsys):
    debugger.breakpoints[4] = "main.hera:7"

    should_continue = debugger.handle_command("break")

    assert should_continue
    assert capsys.readouterr().out == "main.hera:7\n"


def test_print_breakpoints_with_no_breakpoints_set(debugger, capsys):
    should_continue = debugger.handle_command("break")

    assert should_continue
    assert capsys.readouterr().out == "No breakpoints set.\n"


def test_set_breakpoint(debugger):
    assert len(debugger.breakpoints) == 0

    should_continue = debugger.handle_command("break 4")

    assert should_continue
    assert len(debugger.breakpoints) == 1
    assert 0 in debugger.breakpoints
    assert debugger.breakpoints[0] == "test/assets/unit/debugger.hera:4"


def test_set_breakpoint_not_on_line_of_code(debugger, capsys):
    should_continue = debugger.handle_command("break 1")

    assert should_continue
    assert len(debugger.breakpoints) == 0
    assert capsys.readouterr().out == "Error: could not find corresponding line.\n"


def test_set_unparseable_breakpoint(debugger, capsys):
    should_continue = debugger.handle_command("break $$$")

    assert should_continue
    assert len(debugger.breakpoints) == 0
    assert capsys.readouterr().out == "Error: could not locate label `$$$`.\n"


def test_execute_break_with_too_many_args(debugger, capsys):
    should_continue = debugger.handle_command("break 1 2 3")

    assert should_continue
    assert len(debugger.breakpoints) == 0
    assert capsys.readouterr().out == "break takes zero or one arguments.\n"


def test_execute_abbreviated_break(debugger):
    with patch("hera.debugger.Debugger.exec_break") as mock_exec_break:
        debugger.handle_command("b 7")
        assert mock_exec_break.call_count == 1

        args = mock_exec_break.call_args[0]
        assert len(args) == 1
        assert args[0] == ["7"]

        kwargs = mock_exec_break.call_args[1]
        assert len(kwargs) == 0


def test_execute_next(debugger):
    assert debugger.vm.registers[1] == 0
    assert debugger.vm.pc == 0

    should_continue = debugger.handle_command("next")

    assert should_continue
    assert debugger.vm.registers[1] == 3
    assert debugger.vm.pc == 2


def test_execute_next_with_halt(debugger, capsys):
    # Last instruction of SAMPLE_PROGRAM is a HALT operation.
    debugger.vm.pc = len(debugger.program) - 1

    should_continue = debugger.handle_command("next")

    assert should_continue
    assert debugger.vm.pc == len(debugger.program) - 1
    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_execute_next_after_end_of_program(debugger, capsys):
    debugger.vm.pc = 9000

    should_continue = debugger.handle_command("next")

    assert should_continue
    assert debugger.vm.pc == 9000
    assert (
        capsys.readouterr().out
        == "Program has finished executing. Press 'r' to restart.\n"
    )


def test_execute_next_with_too_many_args(debugger, capsys):
    # TODO: It would actually be useful if this worked.
    should_continue = debugger.handle_command("next 10")

    assert should_continue
    assert capsys.readouterr().out == "next takes no arguments.\n"


def test_execute_abbreviated_next(debugger):
    with patch("hera.debugger.Debugger.exec_next") as mock_exec_next:
        debugger.handle_command("n")
        assert mock_exec_next.call_count == 1


def test_execute_continue_with_breakpoint(debugger):
    debugger.breakpoints[4] = ""

    should_continue = debugger.handle_command("continue")

    assert should_continue
    assert debugger.vm.registers[1] == 3
    assert debugger.vm.registers[2] == 39
    assert debugger.vm.registers[3] == 0
    assert debugger.vm.pc == 4

    # Make sure continuing again doesn't loop on the same instruction.
    debugger.handle_command("continue")
    assert debugger.vm.pc == 5


def test_execute_continue_without_breakpoint(debugger, capsys):
    should_continue = debugger.handle_command("continue")

    assert should_continue
    assert debugger.vm.registers[1] == 3
    assert debugger.vm.registers[2] == 39
    assert debugger.vm.registers[3] == 42
    assert debugger.vm.pc == 5
    assert capsys.readouterr().out == "Program has finished executing.\n"


def test_execute_continue_with_too_many_args(debugger, capsys):
    should_continue = debugger.handle_command("continue 10")

    assert should_continue
    assert capsys.readouterr().out == "continue takes no arguments.\n"


def test_execute_abbreviated_continue(debugger):
    with patch("hera.debugger.Debugger.exec_continue") as mock_exec_continue:
        debugger.handle_command("c")
        assert mock_exec_continue.call_count == 1


def test_print_register(debugger, capsys):
    debugger.vm.registers[7] = 42

    should_continue = debugger.handle_command("print r7")

    assert should_continue
    assert capsys.readouterr().out == "r7 = 0x002a = 42 = '*'\n"


def test_print_invalid_register(debugger, capsys):
    should_continue = debugger.handle_command("print r17")

    assert should_continue
    assert capsys.readouterr().out == "r17 is not a valid register.\n"


def test_print_program_counter(debugger, capsys):
    debugger.vm.pc = 7

    should_continue = debugger.handle_command("print PC")

    assert should_continue
    assert capsys.readouterr().out == "PC = 7\n"


def test_print_memory_location(debugger, capsys):
    debugger.vm.assign_memory(97, 1000)

    should_continue = debugger.handle_command("print m[97]")

    assert should_continue
    assert capsys.readouterr().out == "M[97] = 1000\n"


def test_execute_print_with_too_few_args(debugger, capsys):
    # TODO: It would be useful if this printed the last printed expression again.
    should_continue = debugger.handle_command("print")

    assert should_continue
    assert capsys.readouterr().out == "print takes one argument.\n"


def test_execute_abbreviated_print(debugger):
    with patch("hera.debugger.Debugger.exec_print") as mock_exec_print:
        debugger.handle_command("p r7")
        assert mock_exec_print.call_count == 1

        args = mock_exec_print.call_args[0]
        assert len(args) == 1
        assert args[0] == ["r7"]

        kwargs = mock_exec_print.call_args[1]
        assert len(kwargs) == 0


def test_execute_skip(debugger):
    should_continue = debugger.handle_command("skip 2")

    assert should_continue
    assert debugger.vm.pc == 4


def test_execute_skip_with_no_arg(debugger):
    should_continue = debugger.handle_command("skip")

    assert should_continue
    assert debugger.vm.pc == 2


def test_execute_quit(debugger):
    assert debugger.handle_command("quit") is False
    assert debugger.handle_command("q") is False


def test_execute_help(debugger, capsys):
    should_continue = debugger.handle_command("help")

    assert should_continue
    out = capsys.readouterr().out
    assert "Available commands" in out
    assert "Error:" not in out


def test_execute_unknown_command(debugger, capsys):
    should_continue = debugger.handle_command("whatever")

    assert should_continue
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
    assert debugger.get_breakpoint_name(0) == "test/assets/unit/debugger.hera:4"


def test_get_breakpoint_name_with_label(debugger):
    assert debugger.get_breakpoint_name(4) == "test/assets/unit/debugger.hera:7 (add)"


def test_get_breakpoint_name_does_not_include_constant(debugger):
    assert debugger.get_breakpoint_name(3) == "test/assets/unit/debugger.hera:5"


def test_print_current_op(debugger, capsys):
    debugger.print_current_op()

    captured = capsys.readouterr()
    assert (
        captured.out == "[test/assets/unit/debugger.hera, line 4]\n\n0000  SET(R1, 3)\n"
    )
