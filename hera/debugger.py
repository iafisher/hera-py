"""Debug HERA programs.

`debug` is the sole public function.

TODO: Explain why this is all so tricky.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import re
import readline
from typing import Dict, List

from .data import Op
from .symtab import Label
from .utils import op_to_string, print_register_debug, REGISTER_BRANCHES
from .vm import VirtualMachine


def debug(program: List[Op], symbol_table: Dict[str, int]) -> None:
    """Start the debug loop."""
    debugger = Debugger(program, symbol_table)
    debugger.loop()


_HELP_MSG = """\
Available commands:
    break <n>    Set a breakpoint on the n'th line of the program. When no
                 arguments are given, all current breakpoints are printed.

    continue     Execute the program until a breakpoint is encountered or the program
                 terminates.

    help         Print this help message.

    list         Print the current and surrounding lines of source code.

    next         Execute the current line.

    print <e>    Evaluate the expression and print the result. The expression
                 may be a register or a memory location, e.g. "M[123]".

    restart      Restart the execution of the program from the beginning.

    skip <n>     Skip ahead by n instructions without executing them. If not provided,
                 n defaults to 1.

    quit         Exit the debugger.

Command names may be abbreviated with a unique prefix, e.g. "n" for "next".
"""


class Debugger:
    """A class for debugging. External users should generally use the module-level
    `debug` function instead of this class.
    """

    def __init__(self, program, symbol_table):
        self.max_pc = len(program)
        self.program = get_original_program(program, symbol_table)
        self.pc_map = get_pc_map(self.program)

        self.symbol_table = symbol_table
        # A map from instruction numbers (i.e., possible values of the program counter)
        # to human-readable line numbers.
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

            if not self.handle_command(response):
                break

    def handle_command(self, response):
        """Parse the command and execute it. Return False if the loop should exit, and
        True otherwise.
        """
        cmd, *args = response.split()
        cmd = cmd.lower()
        if "break".startswith(cmd):
            self.exec_break(args)
        elif "continue".startswith(cmd):
            self.exec_continue(args)
        elif "list".startswith(cmd):
            self.exec_list(args)
        elif "next".startswith(cmd):
            self.exec_next(args)
        elif "print".startswith(cmd):
            self.exec_print(args)
        elif "restart".startswith(cmd):
            self.exec_restart(args)
        elif "skip".startswith(cmd):
            self.exec_skip(args)
        elif "help".startswith(cmd):
            print(_HELP_MSG)
        elif "quit".startswith(cmd):
            return False
        else:
            print("{} is not a known command.".format(cmd))

        return True

    def exec_break(self, args):
        if len(args) > 1:
            print("break takes zero or one arguments.")
            return

        if len(args) == 0:
            # TODO: In pdb, break with no arguments set a breakpoint at the current
            # line. Should I do that too?
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

        if self.is_finished():
            print("Program has finished executing. Press 'r' to restart.")
            return

        real_ops = self.get_real_ops()
        for real_op in real_ops:
            self.vm.exec_one(real_op)

        if self.is_finished():
            print("Program has finished executing.")
            return

        self.print_current_op()

    def exec_skip(self, args):
        if len(args) > 1:
            print("skip takes zero or one arguments.")
            return

        if len(args) == 1:
            try:
                offset = int(args[0])
            except ValueError as e:
                print("skip takes an integer argument.")
        else:
            offset = 1

        for _ in range(offset):
            real_ops = self.get_real_ops()
            for real_op in real_ops:
                self.vm.exec_one(real_op)

            if self.is_finished():
                print("Program has finished executing.")
                return

        self.print_current_op()

    def exec_list(self, args):
        if len(args) != 0:
            print("list takes no arguments.")
            return

        index = self.pc_map[self.vm.pc]
        previous_three = self.program[max(index - 3, 0) : index]
        next_three = self.program[index + 1 : index + 4]

        first_op = (previous_three[0] if previous_three else self.program[index])[0]
        last_op = (next_three[-1] if next_three else self.program[index])[0]

        if first_op.name.location is not None:
            path = (
                "<stdin>"
                if first_op.name.location.path == "-"
                else first_op.name.location.path
            )
            first_line = first_op.name.location.line
            last_line = last_op.name.location.line
            print("[{}, lines {}-{}]\n".format(path, first_line, last_line))

        for op, _, pc in previous_three:
            print("   {:0>4x}  {}".format(pc, op_to_string(op)))

        op, _, pc = self.program[index]
        print("-> {:0>4x}  {}".format(pc, op_to_string(op)))

        for op, _, pc in next_three:
            print("   {:0>4x}  {}".format(pc, op_to_string(op)))

    def exec_continue(self, args):
        if len(args) != 0:
            print("continue takes no arguments.")
            return

        while True:
            real_ops = self.get_real_ops()
            for real_op in real_ops:
                self.vm.exec_one(real_op)

            if self.is_finished():
                print("Program has finished executing.")
                return
            elif self.vm.pc in self.breakpoints:
                break

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
        """Print the next operation to be executed. If the program has finished
        executed, nothing is printed.
        """
        if not self.is_finished():
            index = self.pc_map[self.vm.pc]
            op = self.program[index][0].original or self.program[index][0]
            opstr = op_to_string(op)
            if op.name.location is not None:
                path = (
                    "<stdin>" if op.name.location.path == "-" else op.name.location.path
                )
                print("[{}, line {}]\n".format(path, op.name.location.line))
            print("{:0>4x}  {}".format(self.vm.pc, opstr))

    def get_real_ops(self, pc=None):
        if pc is None:
            pc = self.vm.pc

        return self.program[self.pc_map[self.vm.pc]][1]

    def resolve_location(self, b):
        """Resolve a user-supplied location string into an instruction number"""
        try:
            lineno = int(b)
        except ValueError:
            try:
                opno = self.symbol_table[b]
                assert isinstance(opno, Label)
                return opno
            except (KeyError, AssertionError):
                raise ValueError("could not locate label `{}`.".format(b)) from None
        else:
            for op, _, pc in self.program:
                if op.name.location.line == lineno:
                    return pc

            raise ValueError("could not find corresponding line.")

    def get_breakpoint_name(self, b):
        """Turn an instruction number into a human-readable location string with the
        file path and line number. More or less the inverse of `resolve_location`.
        """
        index = self.pc_map[b]
        op = self.program[index][0].original or self.program[index][0]
        if op.name.location is not None:
            path = "<stdin>" if op.name.location.path == "-" else op.name.location.path
            loc = path + ":" + str(op.name.location.line)
        else:
            loc = str(op.name.location.line)

        # Look for a label corresponding to the breakpoint.
        for symbol, value in self.symbol_table.items():
            if value == b and isinstance(value, Label):
                return "{} ({})".format(loc, symbol)

        return loc

    def is_finished(self):
        return self.vm.halted or self.vm.pc >= self.max_pc


def get_original_program(program, symbol_table):
    """Given a preprocessed program and its symbol table, return the original ops of the
    program in a list of (original, real, pc) triples, where `real` is a list of the ops
    that `original` was preprocssed to and `pc` is the program counter corresponding to
    `real[0]`, e.g. a SETLO/SETHI sequence would yield (SET, [SETLO, SETHI], 0).
    """
    if not program:
        return []

    original_program = []

    original_op = program[0].original
    real_ops = []
    real_pc = 0
    for pc, op in enumerate(program + [Op("DUMMY", [])]):
        if op.original == original_op:
            real_ops.append(op)
        else:
            # Substitute label values for their names.
            if original_op.name in REGISTER_BRANCHES and isinstance(
                original_op.args[0], int
            ):
                original_label = reverse_lookup_label(symbol_table, original_op.args[0])
                if original_label is not None:
                    original_op.args[0] = original_label

            original_program.append((original_op, real_ops, real_pc))
            original_op = op.original
            real_ops = [op]
            real_pc = pc

    return original_program


def get_pc_map(original_program):
    """Given an original program as returned by `get_original_program`, return a
    dictionary that maps from the virtual machine's program counter to indices in the
    original program.
    """
    if not original_program:
        return {}

    pc_map = {}
    for i, (_, real_ops, pc) in enumerate(original_program):
        for offset in range(len(real_ops)):
            pc_map[pc + offset] = i
    return pc_map


def reverse_lookup_label(symbol_table, value):
    """Return the name of the label that maps to `value`, or None if no such label is
    found. Constants and data labels are ignored.
    """
    for k, v in symbol_table.items():
        if value == v and isinstance(v, Label):
            return k
    return None
