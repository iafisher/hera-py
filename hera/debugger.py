"""Debug HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
import re
import readline

from hera.utils import op_to_string, print_register_debug
from hera.vm import VirtualMachine


def debug(program):
    """Start the debug loop with the given program."""
    debugger = Debugger(program)
    debugger.loop()


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


class Debugger:
    """A class for debugging. External users should generally use the module-level
    `debug` function instead of this class.
    """

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
            elif "jump".startswith(cmd):
                self.exec_jump(args)
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
            try:
                b = self.resolve_location(args[0])
            except ValueError as e:
                print("Error:", e)
            else:
                self.breakpoints[b] = self.get_breakpoint_name(b)

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
            opc = self.vm.pc
            self.vm.exec_one(self.program[self.vm.pc])
            if opc == self.vm.pc:
                print("Program has finished executing.")
                return

        self.print_current_op()

    def exec_jump(self, args):
        if len(args) != 1:
            print("jump takes on argument.")
            return

        try:
            b = self.resolve_location(args[0])
        except ValueError as e:
            print("Error:", e)
        else:
            self.vm.pc = b
            self.print_current_op()

    def exec_continue(self, args):
        if len(args) != 0:
            print("continue takes no arguments.")
            return

        while self.vm.pc < len(self.program) and self.vm.pc not in self.breakpoints:
            opc = self.vm.pc
            self.vm.exec_one(self.program[self.vm.pc])
            if self.vm.pc == opc:
                print("Program has finished executing.")
                return

        self.print_current_op()

    # Match strings of the form "m[123]"
    _MEM_PATTERN = re.compile(r"[Mm]\[([0-9]+)\]")

    def exec_print(self, args):
        if len(args) != 1:
            print("print takes one argument.")
            return

        match = self._MEM_PATTERN.match(args[0])
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
                path = "<stdin>" if op.location.path == "-" else op.location.path
                print("[{}, line {}]\n".format(path, op.name.line))
            print("{:0>4x}  {}".format(self.vm.pc, opstr))

    def resolve_location(self, b):
        try:
            b = int(b)
        except ValueError:
            raise ValueError("could not parse argument.") from None

        for i, op in enumerate(self.program):
            if op.name.line == b:
                return i

        raise ValueError("could not find corresponding line.")

    def get_breakpoint_name(self, b):
        op = self.program[b].original or self.program[b]
        if op.location is not None:
            path = "<stdin>" if op.location.path == "-" else op.location.path
            return path + ":" + str(op.name.line)
        else:
            return str(op.name.line)
