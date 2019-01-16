"""Debug HERA programs.

`debug` is the sole public function.

The code in this module makes an important distinction between "real ops" and "original
ops." Original ops are the HERA operations as they appear in the program that the user
wrote. Real ops are the original ops transformed by the preprocessor into something that
the virtual machine can actually run. For example, a single original SET op corresponds
to two real ops, SETLO and SETHI.

Internally, the debugger operates on real ops, but whenever it displays output to the
user, it must be in terms of original ops.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import re
import readline
from typing import Dict, List

from .data import Op
from .loader import load_program
from .typechecker import Label
from .utils import BRANCHES, DATA_STATEMENTS, op_to_string, print_register_debug, REGISTER_BRANCHES
from .vm import VirtualMachine


def debug(program: List[Op], symbol_table: Dict[str, int]) -> None:
    """Start the debug loop."""
    debugger = Debugger(program, symbol_table)
    debugger.loop()


_HELP_MSG = """\
Available commands:
    break <n>     Set a breakpoint on the n'th line of the program. When no
                  arguments are given, all current breakpoints are printed.

    continue      Execute the program until a breakpoint is encountered or the
                  program terminates.

    execute <op>  Execute a HERA operation. Only non-branching operations may
                  be executed.

    help          Print this help message.

    list <n>      Print the current lines of source code and the n previous and
                  next lines. If not provided, n defaults to 3.

    longlist      Print the entire program.

    next          Execute the current line.

    print <e>     Evaluate the expression and print the result. The expression
                  may be a register or a memory location, e.g. "M[123]".

    restart       Restart the execution of the program from the beginning.

    skip <n>      Skip the next n instructions without executing them. If not
                  provided, n defaults to 1.

    quit          Exit the debugger.

Command names can generally be abbreviated with a unique prefix, e.g. "n" for
"next".
"""


class Debugger:
    """A class for debugging. External users should generally use the module-level
    `debug` function instead of this class.
    """

    def __init__(self, program, symbol_table):
        self.program = program
        self.symbol_table = symbol_table
        # A map from instruction numbers (i.e., possible values of the program counter)
        # to human-readable line numbers.
        self.breakpoints = {}
        self.vm = VirtualMachine()

    def loop(self):
        if not self.program:
            print("Cannot debug an empty program.")
            return

        self.print_current_op()

        while True:
            try:
                response = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not response:
                continue
            elif "quit".startswith(response.lower()):
                break
            else:
                self.handle_command(response)

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
        elif "execute".startswith(cmd):
            self.exec_execute(" ".join(args))
        elif "list".startswith(cmd):
            self.exec_list(args)
        elif cmd == "longlist" or cmd == "ll":
            self.exec_long_list(args)
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
        else:
            print("{} is not a known command.".format(cmd))

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
                break

        self.print_current_op()

    def exec_execute(self, args):
        try:
            ops, _ = load_program(args)
        except SystemExit:
            return

        for op in ops:
            if op.name in BRANCHES or op.name in ("CALL", "RETURN"):
                print("execute cannot take branching operations.")
                return
            elif op.name in DATA_STATEMENTS:
                print("execute cannot take data statements.")
                return

        opc = self.vm.pc
        for op in ops:
            self.vm.exec_one(op)
        self.vm.pc = opc

    def exec_list(self, args):
        if len(args) > 1:
            print("list takes zero or one arguments.")
            return

        try:
            context = int(args[0], base=0) if args else 3
        except ValueError:
            print("Could not parse argument to list.")
            return

        previous_ops = self.get_previous_ops(context)
        next_ops = self.get_next_ops(context)

        first_op = previous_ops[0][1] if previous_ops else self.program[self.vm.pc]
        last_op = next_ops[-1][1] if next_ops else self.program[self.vm.pc]

        if first_op.name.location is not None:
            path = (
                "<stdin>"
                if first_op.name.location.path == "-"
                else first_op.name.location.path
            )
            first_line = first_op.name.location.line
            last_line = last_op.name.location.line
            print("[{}, lines {}-{}]\n".format(path, first_line, last_line))

        for pc, op in previous_ops:
            print("   {:0>4x}  {}".format(pc, op_to_string(op)))

        op = self.program[self.vm.pc].original
        print("-> {:0>4x}  {}".format(self.vm.pc, op_to_string(op)))

        for pc, op in next_ops:
            print("   {:0>4x}  {}".format(pc, op_to_string(op)))

    def exec_long_list(self, args):
        if len(args) != 0:
            print("longlist takes no arguments.")
            return

        index = 0
        while index < len(self.program):
            op = self.program[index].original
            prefix = "-> " if index == self.vm.pc else "   "
            print(prefix + "{:0>4x}  {}".format(index, op_to_string(op)))
            original = self.program[index].original
            while (
                index < len(self.program) and self.program[index].original == original
            ):
                index += 1

    def exec_continue(self, args):
        if len(args) != 0:
            print("continue takes no arguments.")
            return

        while True:
            real_ops = self.get_real_ops()
            for real_op in real_ops:
                self.vm.exec_one(real_op)

            if self.is_finished() or self.vm.pc in self.breakpoints:
                break

        self.print_current_op()

    # Match strings of the form "m[123]"
    _MEM_PATTERN = re.compile(r"[Mm]\[(.*?)\]")

    def exec_print(self, args):
        if len(args) != 1:
            print("print takes one argument.")
            return

        match = self._MEM_PATTERN.match(args[0])
        if match:
            index_str = match.group(1)
            try:
                index = int(index_str, base=0)
            except ValueError:
                # If it's not an integer, try parsing it as a register.
                try:
                    index = self.vm.get_register(index_str)
                except ValueError:
                    print("Could not parse memory location.")
                    return

            print("M[{}] = {}".format(index, self.vm.access_memory(index)))
        elif args[0].lower() == "pc":
            print("PC = {}".format(self.vm.pc))
        else:
            try:
                v = self.vm.get_register(args[0])
            except ValueError:
                # If it's not a register, see if it's in the symbol table.
                try:
                    v = self.symbol_table[args[0]]
                except KeyError:
                    print("Could not parse argument to print.")
                else:
                    print("{} = {}".format(args[0], v))
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
            op = self.program[self.vm.pc].original or self.program[self.vm.pc]
            opstr = op_to_string(op)
            if op.name.location is not None:
                path = (
                    "<stdin>" if op.name.location.path == "-" else op.name.location.path
                )
                print("[{}, line {}]\n".format(path, op.name.location.line))
            print("{:0>4x}  {}".format(self.vm.pc, opstr))
        else:
            print("Program has finished executing.")

    def get_real_ops(self):
        """Return all the real ops that correspond to the current original op. See
        module docstring for explanation of terminology.
        """
        original = self.program[self.vm.pc].original
        end = self.vm.pc
        while end < len(self.program) and self.program[end].original == original:
            end += 1

        return self.program[self.vm.pc : end]

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
            for pc, op in enumerate(self.program):
                if op.name.location.line == lineno:
                    return pc

            raise ValueError("could not find corresponding line.")

    def get_breakpoint_name(self, b):
        """Turn an instruction number into a human-readable location string with the
        file path and line number. More or less the inverse of `resolve_location`.
        """
        op = self.program[b].original or self.program[b]
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

    def get_previous_ops(self, n):
        """Return the `n` original ops before the current one."""
        # TODO: Refactor this.
        if self.vm.pc == 0:
            return []

        ops = []
        index = self.vm.pc - 1
        for _ in range(n):
            original = self.program[index].original
            while index >= 0 and self.program[index].original == original:
                index -= 1
            ops.append((index + 1, self.program[index + 1].original))
            if index < 0:
                break
        return list(reversed(ops))

    def get_next_ops(self, n):
        """Return the `n` original ops after the current one."""
        ops = []
        index = self.vm.pc
        for _ in range(n):
            original = self.program[index].original
            while (
                index < len(self.program) and self.program[index].original == original
            ):
                index += 1
            if index < len(self.program):
                ops.append((index, self.program[index].original))
            else:
                break
        return ops

    def is_finished(self):
        return self.vm.halted or self.vm.pc >= len(self.program)


def reverse_lookup_label(symbol_table, value):
    """Return the name of the label that maps to `value`, or None if no such label is
    found. Constants and data labels are ignored.
    """
    for k, v in symbol_table.items():
        if value == v and isinstance(v, Label):
            return k
    return None
