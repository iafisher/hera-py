import re
import readline

from hera.utils import op_to_string, print_register_debug
from hera.vm import VirtualMachine


# Match strings of the form "m[123]"
_MEM_PATTERN = re.compile(r"[Mm]\[([0-9]+)\]")
_HELP_MSG = """\
Available commands:
    help         Print this help message.

    next         Execute the current line.

    print <e>    Evaluate the expression and print its result. The expression
                 may be a register or a memory location, e.g. "M[123]".

    quit         Exit the debugger.

Command names may be abbreviated with a unique prefix, e.g. "n" for "next".
"""


def run_debug_loop(program):
    vm = VirtualMachine()
    print(op_to_string(program[0]))

    while vm.pc < len(program):
        try:
            response = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not response:
            continue

        cmd, *args = response.split()
        cmd = cmd.lower()
        if "next".startswith(cmd):
            if len(args) != 0:
                print("next takes no arguments.")
                continue

            vm.exec_one(program[vm.pc])
            print(op_to_string(program[vm.pc]))
        elif "print".startswith(cmd):
            if len(args) != 1:
                print("print takes one argument.")
                continue

            match = _MEM_PATTERN.match(args[0])
            if match:
                index = int(match.group(1))
                print("M[{}] = {}".format(index, vm.access_memory(index)))
            else:
                try:
                    v = vm.get_register(args[0])
                except ValueError:
                    print("{} is not a valid register.".format(args[0]))
                else:
                    print_register_debug(args[0], v, to_stderr=False)
        elif "quit".startswith(cmd):
            break
        elif "help".startswith(cmd):
            print(_HELP_MSG)
        else:
            print('Unknown command "{}"'.format(cmd))
