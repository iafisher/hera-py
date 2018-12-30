import re
import readline

from hera.utils import op_to_string, print_register_debug
from hera.vm import VirtualMachine


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


def debug(program):
    debugger = Debugger(program)
    debugger.loop()


class Debugger:
    def __init__(self, program):
        self.program = program
        self.breakpoints = {}
        self.vm = VirtualMachine()

    def loop(self):
        self.print_current_op()

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
                self.exec_break(args)
            elif "continue".startswith(cmd):
                self.exec_continue(args)
            elif "next".startswith(cmd):
                self.exec_next(args)
            elif "print".startswith(cmd):
                self.exec_print(args)
            elif "restart".startswith(cmd):
                self.exec_restart(args)
            elif "quit".startswith(cmd):
                break
            elif "help".startswith(cmd):
                print(_HELP_MSG)
            else:
                print('Unknown command "{}"'.format(cmd))

    def exec_break(self, args):
        if len(args) > 1:
            print("break takes zero or one arguments.")
            return

        if len(args) == 0:
            if self.breakpoints:
                for b in self.breakpoints.values():
                    print(b)
            else:
                print("No breakpoints set.")
        else:
            b = self.resolve_breakpoint(args[0])
            if b != -1:
                self.breakpoints[b] = self.get_breakpoint_name(b)
            else:
                print("Could not parse argument to break.")

    def exec_next(self, args):
        if len(args) != 0:
            print("next takes no arguments.")
            return

        if self.vm.pc >= len(self.program):
            print("Program has finished executing. Press 'r' to restart.")
            return

        original_op = self.program[self.vm.pc].original
        while (
            self.vm.pc < len(self.program)
            and self.program[self.vm.pc].original == original_op
        ):
            self.vm.exec_one(self.program[self.vm.pc])

        self.print_current_op()

    def exec_continue(self, args):
        if len(args) != 0:
            print("continue takes no arguments.")
            return

        while self.vm.pc < len(self.program) and self.vm.pc not in self.breakpoints:
            self.vm.exec_one(self.program[self.vm.pc])

        self.print_current_op()

    # Match strings of the form "m[123]"
    _MEM_PATTERN = re.compile(r"[Mm]\[([0-9]+)\]")

    def exec_print(self, args):
        if len(args) != 1:
            print("print takes one argument.")
            return

        match = _MEM_PATTERN.match(args[0])
        if match:
            index = int(match.group(1))
            print("M[{}] = {}".format(index, self.vm.access_memory(index)))
        elif args[0].lower() == "pc":
            print("PC = {}".format(self.vm.pc))
        else:
            try:
                v = self.vm.get_register(args[0])
            except ValueError:
                print("{} is not a valid register.".format(args[0]))
            else:
                print_register_debug(args[0], v, to_stderr=False)

    def exec_restart(self, args):
        if len(args) != 0:
            print("restart takes no arguments.")
            return

        self.vm.reset()
        self.print_current_op()

    def print_current_op(self):
        if self.vm.pc < len(self.program):
            op = self.program[self.vm.pc].original or self.program[self.vm.pc]
            opstr = op_to_string(op)
            if op.location is not None:
                print("[{}, line {}]\n".format(op.location.path, op.name.line))
            print("{:0>4x}  {}".format(self.vm.pc, opstr))

    def resolve_breakpoint(self, b):
        try:
            b = int(b)
        except ValueError:
            return -1

        for i, op in enumerate(self.program):
            if op.name.line == b:
                return i

        return -1

    def get_breakpoint_name(self, b):
        op = self.program[b].original or self.program[b]
        if op.location is not None:
            return op.location.path + ":" + str(op.name.line)
        else:
            return str(op.name.line)
