"""Test programs generated by a compiler for the Tiger language implemented for CS350.
"""
import json
from io import StringIO
from unittest.mock import patch

from .utils import execute_program_helper

from hera.main import main
from hera.utils import from_u16


def helper_stdlib(f, *args):
    """Construct a HERA program that calls the Tiger function named `f` with the given
    arguments.
    """
    data = ""
    for i, arg in enumerate(args):
        if isinstance(arg, str):
            data += "DLABEL(arg{})\nLP_STRING({})\n".format(i, json.dumps(arg))

    preamble = """\
#include <Tiger-stdlib-stack-data.hera>

CBON()
MOVE(R12, SP)
INC(SP, {})
"""
    preamble = preamble.format(len(args) + 3)

    load_args = ""
    for i, arg in enumerate(args):
        if isinstance(arg, str):
            load_args += "SET(R1, arg{})\nSTORE(R1, {}, R12)\n".format(i, i + 3)
        else:
            load_args += "SET(R1, {})\nSTORE(R1, {}, R12)\n".format(arg, i + 3)

    epilogue = """\
CALL(R12, {})
LOAD(R1, 3, R12)
DEC(SP, {})
HALT()

#include <Tiger-stdlib-stack.hera>
    """
    epilogue = epilogue.format(f, len(args) + 3)

    return data + preamble + load_args + epilogue


def test_div_and_print(capsys):
    main(["test/assets/cs350/div_and_print.hera"])

    captured = capsys.readouterr()
    assert captured.out == "5"


def test_merge_sort(capsys):
    main(["test/assets/cs350/merge_sort.hera"])

    captured = capsys.readouterr()
    assert captured.out == "42"


def test_lexical_scope_deep(capsys):
    main(["test/assets/cs350/lexical_scope_deep.hera"])

    captured = capsys.readouterr()
    assert captured.out == "42"


def test_stdlib_ord():
    vm = execute_program_helper(helper_stdlib("ord", "A"))

    assert vm.registers[1] == 65


def test_stdlib_chr():
    vm = execute_program_helper(helper_stdlib("chr", 65))

    addr = vm.registers[1]
    assert vm.load_memory(addr) == 1
    assert vm.load_memory(addr + 1) == 65


def test_stdlib_size():
    vm = execute_program_helper(helper_stdlib("size", "hello"))

    assert vm.registers[1] == 5


def test_stdlib_substring():
    vm = execute_program_helper(helper_stdlib("substring", "hello", 1, 2))

    addr = vm.registers[1]
    assert vm.load_memory(addr) == 2
    assert vm.load_memory(addr + 1) == ord("e")
    assert vm.load_memory(addr + 2) == ord("l")


def test_stdlib_concat():
    vm = execute_program_helper(helper_stdlib("concat", "ab", "cd"))

    addr = vm.registers[1]
    assert vm.load_memory(addr) == 4
    assert vm.load_memory(addr + 1) == ord("a")
    assert vm.load_memory(addr + 2) == ord("b")
    assert vm.load_memory(addr + 3) == ord("c")
    assert vm.load_memory(addr + 4) == ord("d")


def test_stdlib_tstrcmp():
    vm = execute_program_helper(helper_stdlib("tstrcmp", "a", "b"))

    assert from_u16(vm.registers[1]) < 0


def test_stdlib_div():
    vm = execute_program_helper(helper_stdlib("div", 42, 6))

    assert vm.registers[1] == 7


def test_stdlib_mod():
    vm = execute_program_helper(helper_stdlib("mod", 10, 3))

    assert vm.registers[1] == 1


def test_stdlib_not():
    vm = execute_program_helper(helper_stdlib("not", 1))

    assert vm.registers[1] == 0


def test_stdlib_getchar_ord():
    with patch("sys.stdin", StringIO("abc\n")):
        vm = main(["test/assets/cs350/getchar_ord.hera"])

    assert vm.registers[1] == ord("a")


def test_stdlib_getchar(capsys):
    with patch("sys.stdin", StringIO("abc\n")):
        vm = main(["test/assets/cs350/getchar.hera"])

    addr = vm.registers[1]
    assert vm.memory[addr] == 1
    assert vm.memory[addr + 1] == ord("a")


def test_stdlib_putchar_ord(capsys):
    execute_program_helper(helper_stdlib("putchar_ord", 98))

    assert capsys.readouterr().out == "b"


def test_stdlib_flush():
    # Just making sure it doesn't raise any SystemExit exceptions.
    execute_program_helper(helper_stdlib("flush"))


def test_stdlib_printint(capsys):
    execute_program_helper(helper_stdlib("printint", -42))

    assert capsys.readouterr().out == "-42"


def test_stdlib_printbool(capsys):
    execute_program_helper(helper_stdlib("printbool", 1))

    assert capsys.readouterr().out == "true"


def test_stdlib_print(capsys):
    execute_program_helper(helper_stdlib("print", "hello"))

    assert capsys.readouterr().out == "hello"


def test_stdlib_println(capsys):
    execute_program_helper(helper_stdlib("println", "hello"))

    assert capsys.readouterr().out == "hello\n"


def test_stdlib_ungetchar():
    vm = execute_program_helper(helper_stdlib("ungetchar"))

    assert vm.input_pos == -1


def test_stdlib_getline():
    with patch("sys.stdin", StringIO("hello\n")):
        vm = main(["test/assets/cs350/getline.hera"])

    addr = vm.registers[1]
    assert vm.memory[addr] == 5
    assert vm.memory[addr + 1] == ord("h")
    assert vm.memory[addr + 2] == ord("e")
    assert vm.memory[addr + 3] == ord("l")
    assert vm.memory[addr + 4] == ord("l")
    assert vm.memory[addr + 5] == ord("o")
