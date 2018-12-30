import re
import readline

from hera.utils import op_to_string, print_register_debug
from hera.vm import VirtualMachine


# Match strings of the form "m[123]"
_MEM_PATTERN = re.compile(r"[Mm]\[([0-9]+)\]")
_HELP_MSG = """\
Available commands:
    break <n>    Set a breakpoint on the n'th line of the program. When no
                 arguments are given, all current breakpoints are printed.

    help         Print this help message.

    next         Execute the current line.

    print <e>    Evaluate the expression and print its result. The expression
                 may be a register or a memory location, e.g. "M[123]".

    restart      Restart the execution of the program from the beginning.

    quit         Exit the debugger.

Command names may be abbreviated with a unique prefix, e.g. "n" for "next".
"""


def run_debug_loop(program):
    breakpoints = {}
    vm = VirtualMachine()
    print_current_op(program, vm)

    while True:
        try:
            response = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not response:
            continue

        cmd, *args = response.split()
        cmd = cmd.lower()
        if "break".startswith(cmd):
            if len(args) > 1:
                print("break takes zero or one arguments.")
                continue

            if len(args) == 0:
                if breakpoints:
                    for b in breakpoints.values():
                        print(b)
                else:
                    print("No breakpoints set.")
            else:
                b = resolve_breakpoint(program, args[0])
                if b != -1:
                    breakpoints[b] = get_breakpoint_name(program, b)
                else:
                    print("Could not parse argument to break.")
        elif "next".startswith(cmd):
            if len(args) != 0:
                print("next takes no arguments.")
                continue

            if vm.pc >= len(program):
                print("Program has finished executing. Press 'r' to restart.")
                continue

            original_op = program[vm.pc].original
            while vm.pc < len(program) and program[vm.pc].original == original_op:
                vm.exec_one(program[vm.pc])

            print_current_op(program, vm)
        elif "continue".startswith(cmd):
            if len(args) != 0:
                print("continue takes no arguments.")
                continue

            while vm.pc < len(program) and vm.pc not in breakpoints:
                vm.exec_one(program[vm.pc])

            print_current_op(program, vm)
        elif "print".startswith(cmd):
            if len(args) != 1:
                print("print takes one argument.")
                continue

            match = _MEM_PATTERN.match(args[0])
            if match:
                index = int(match.group(1))
                print("M[{}] = {}".format(index, vm.access_memory(index)))
            elif args[0].lower() == "pc":
                print("PC = {}".format(vm.pc))
            else:
                try:
                    v = vm.get_register(args[0])
                except ValueError:
                    print("{} is not a valid register.".format(args[0]))
                else:
                    print_register_debug(args[0], v, to_stderr=False)
        elif "restart".startswith(cmd):
            if len(args) != 0:
                print("restart takes no arguments.")
                continue

            vm.reset()
            print_current_op(program, vm)
        elif "quit".startswith(cmd):
            break
        elif "help".startswith(cmd):
            print(_HELP_MSG)
        else:
            print('Unknown command "{}"'.format(cmd))


def print_current_op(program, vm):
    if vm.pc < len(program):
        op = program[vm.pc].original or program[vm.pc]
        opstr = op_to_string(op)
        if op.location is not None:
            print("[{}, line {}]\n".format(op.location.path, op.name.line))
        print("{:0>4x}  {}".format(vm.pc, opstr))


def resolve_breakpoint(program, b):
    try:
        b = int(b)
    except ValueError:
        return -1

    for i, op in enumerate(program):
        if op.name.line == b:
            return i

    return -1


def get_breakpoint_name(program, b):
    op = program[b].original or program[b]
    if op.location is not None:
        return op.location.path + ":" + str(op.name.line)
    else:
        return str(op.name.line)
