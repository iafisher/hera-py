import pytest
from unittest.mock import patch

from hera.data import Op
from hera.debugger import (
    Debugger,
    get_original_program,
    get_pc_map,
    reverse_lookup_label,
)
from hera.loader import load_program, load_program_from_file
from hera.symtab import Constant, Label


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

        args, kwargs = mock_exec_break.call_args
        assert len(args) == 1
        assert args[0] == ["7"]
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
    debugger.vm.pc = 5

    should_continue = debugger.handle_command("next")

    assert should_continue
    assert debugger.vm.pc == 5
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

        args, kwargs = mock_exec_print.call_args
        assert len(args) == 1
        assert args[0] == ["r7"]
        assert len(kwargs) == 0


def test_execute_skip(debugger):
    should_continue = debugger.handle_command("skip 2")

    assert should_continue
    assert debugger.vm.pc == 4


def test_execute_skip_with_no_arg(debugger):
    should_continue = debugger.handle_command("skip")

    assert should_continue
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
    should_continue = debugger.handle_command("list")

    assert should_continue
    captured = capsys.readouterr().out
    assert (
        captured
        == """\
[test/assets/unit/debugger, lines 4-8]

-> 0000  SET(R1, 3)
   0002  SET(R2, 39)
   0004  ADD(R3, R1, R2)
   0005  HALT()\n
"""
    )


def test_execute_abbreviated_list(debugger):
    with patch("hera.debugger.Debugger.exec_list") as mock_exec_list:
        debugger.handle_command("l")
        assert mock_exec_list.call_count == 1


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


def test_get_original_program():
    set_op = Op("SET", ["R1", 10])
    setlo_op = Op("SETLO", ["R1", 10], original=set_op)
    sethi_op = Op("SETHI", ["R1", 0], original=set_op)
    add_op = Op("ADD", ["R2", "R1", "R0"])
    add_op = add_op._replace(original=add_op)
    program = [setlo_op, sethi_op, add_op]
    assert get_original_program(program, {}) == [
        (set_op, [setlo_op, sethi_op], 0),
        (add_op, [add_op], 2),
    ]


ORIGINAL_PROGRAM_EXAMPLE = """\
CBON()
// n in R1, answer in R2
SET(R1, 7)
SET(R2, 1)
CMP(R0, R1)
BZ(end)

// i in R3
MOVE(R3, R1)
LABEL(loop)
CMP(R3, R0)
BZ(end)
MUL(R2, R2, R3)
DEC(R3, 1)
BR(loop)

LABEL(end)
"""


def test_get_original_program_with_large_example():
    program, symbol_table = load_program(ORIGINAL_PROGRAM_EXAMPLE)
    original_program = get_original_program(program, symbol_table)
    assert original_program == [
        (Op("CBON", []), [Op("FON", [0x10])], 0),
        (Op("SET", ["R1", 7]), [Op("SETLO", ["R1", 7]), Op("SETHI", ["R1", 0])], 1),
        (Op("SET", ["R2", 1]), [Op("SETLO", ["R2", 1]), Op("SETHI", ["R2", 0])], 3),
        (Op("CMP", ["R0", "R1"]), [Op("FON", [0x8]), Op("SUB", ["R0", "R0", "R1"])], 5),
        (
            Op("BZ", ["end"]),
            [Op("SETLO", ["R11", 21]), Op("SETHI", ["R11", 0]), Op("BZ", ["R11"])],
            7,
        ),
        (Op("MOVE", ["R3", "R1"]), [Op("OR", ["R3", "R1", "R0"])], 10),
        (
            Op("CMP", ["R3", "R0"]),
            [Op("FON", [0x8]), Op("SUB", ["R0", "R3", "R0"])],
            11,
        ),
        (
            Op("BZ", ["end"]),
            [Op("SETLO", ["R11", 21]), Op("SETHI", ["R11", 0]), Op("BZ", ["R11"])],
            13,
        ),
        (Op("MUL", ["R2", "R2", "R3"]), [Op("MUL", ["R2", "R2", "R3"])], 16),
        (Op("DEC", ["R3", 1]), [Op("DEC", ["R3", 1])], 17),
        (
            Op("BR", ["loop"]),
            [Op("SETLO", ["R11", 11]), Op("SETHI", ["R11", 0]), Op("BR", ["R11"])],
            18,
        ),
    ]


def test_get_pc_map_with_large_example():
    pc_map = get_pc_map(get_original_program(*load_program(ORIGINAL_PROGRAM_EXAMPLE)))
    assert pc_map == {
        0: 0,
        1: 1,
        2: 1,
        3: 2,
        4: 2,
        5: 3,
        6: 3,
        7: 4,
        8: 4,
        9: 4,
        10: 5,
        11: 6,
        12: 6,
        13: 7,
        14: 7,
        15: 7,
        16: 8,
        17: 9,
        18: 10,
        19: 10,
        20: 10,
    }


def test_reverse_lookup_label():
    symbol_table = {"n": Constant(11), "end": Label(11)}
    assert reverse_lookup_label(symbol_table, 11) == "end"
    assert reverse_lookup_label(symbol_table, 12) == None
