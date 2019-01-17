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
import readline
from collections import defaultdict
from contextlib import suppress
from typing import Dict, List

from . import minilanguage
from .data import HERAError, Op
from .loader import load_program
from .minilanguage import AssignNode, IntNode, MemoryNode, RegisterNode, SymbolNode
from .typechecker import Constant, DataLabel, Label
from .utils import BRANCHES, DATA_STATEMENTS, op_to_string, print_register_debug
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

    restart       Restart the execution of the program from the beginning.

    skip <n>      Skip the next n instructions without executing them. If not
                  provided, n defaults to 1.

    symbols       Print all symbols the debugger is aware of.

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
        # A map from instruction numbers to lists of labels.
        self.reverse_labels = get_reverse_labels(symbol_table)
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
        try:
            cmd, line = response.split(maxsplit=1)
        except ValueError:
            cmd = response
            line = ""

        args = line.split()
        cmd = cmd.lower()
        if "break".startswith(cmd):
            self.handle_break(args)
        elif "continue".startswith(cmd):
            self.handle_continue(args)
        elif "execute".startswith(cmd):
            self.handle_execute(line)
        elif "list".startswith(cmd):
            self.handle_list(args)
        elif cmd == "longlist" or cmd == "ll":
            self.handle_long_list(args)
        elif "next".startswith(cmd):
            self.handle_next(args)
        elif "restart".startswith(cmd):
            self.handle_restart(args)
        elif cmd == "rr":
            self.handle_rr(args)
        elif "skip".startswith(cmd):
            self.handle_skip(args)
        elif cmd.startswith("sym") and "symbols".startswith(cmd):
            self.handle_symbols(args)
        elif "help".startswith(cmd):
            print(_HELP_MSG)
        else:
            self.handle_expression(response)

    def handle_break(self, args):
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

    def handle_next(self, args):
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

    def handle_symbols(self, args):
        if len(args) != 0:
            print("symbols takes no arguments.")
            return

        sorted_pairs = sorted(self.symbol_table.items(), key=lambda t: t[0].lower())
        for k, v in sorted_pairs:
            self.print_symbol(k, v)

    def handle_skip(self, args):
        if len(args) > 1:
            print("skip takes zero or one arguments.")
            return

        if len(args) == 1:
            try:
                offset = int(args[0])
            except ValueError:
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

    def handle_execute(self, line):
        try:
            ops, _ = load_program(line)
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

    def handle_list(self, args):
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

        for pc, _ in previous_ops:
            self.print_op(pc)

        self.print_op(self.vm.pc)

        for pc, _ in next_ops:
            self.print_op(pc)

    def handle_long_list(self, args):
        if len(args) != 0:
            print("longlist takes no arguments.")
            return

        index = 0
        while index < len(self.program):
            original = self.program[index].original
            self.print_op(index)
            while (
                index < len(self.program) and self.program[index].original == original
            ):
                index += 1

    def handle_continue(self, args):
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

    def handle_restart(self, args):
        if len(args) != 0:
            print("restart takes no arguments.")
            return

        self.vm.reset()
        self.print_current_op()

    def handle_rr(self, args):
        if len(args) != 0:
            print("rr takes no arguments.")
            return

        if all(r == 0 for r in self.vm.registers):
            print("All registers are set to zero.")
        else:
            last_non_zero = 15
            while self.vm.registers[last_non_zero] == 0:
                last_non_zero -= 1

            if last_non_zero < 13:
                for i in range(1, last_non_zero + 1):
                    print_register_debug(
                        "R" + str(i), self.vm.registers[i], to_stderr=False
                    )
                print("\nAll higher registers are set to zero.")
            else:
                for i, v in enumerate(self.vm.registers[1:], start=1):
                    print_register_debug("R" + str(i), v, to_stderr=False)

    def handle_expression(self, line):
        try:
            tree = minilanguage.parse(line)
        except SyntaxError as e:
            msg = str(e)
            if msg:
                print("Parse error: " + msg + ".")
            else:
                print("Parse error.")
            return

        try:
            if isinstance(tree, AssignNode):
                rhs = self.evaluate_node(tree.rhs)
                if isinstance(tree.lhs, RegisterNode):
                    if tree.lhs.value == "pc":
                        self.vm.pc = rhs
                    else:
                        self.vm.store_register(tree.lhs.value, rhs)
                else:
                    address = self.evaluate_node(tree.lhs.address)
                    self.vm.assign_memory(address, rhs)
            elif isinstance(tree, RegisterNode):
                if tree.value == "pc":
                    print("PC = {}".format(self.vm.pc))
                else:
                    value = self.vm.get_register(tree.value)
                    print_register_debug(tree.value, value, to_stderr=False)
            elif isinstance(tree, MemoryNode):
                address = self.evaluate_node(tree.address)
                print("M[{}] = {}".format(address, self.vm.access_memory(address)))
            elif isinstance(tree, SymbolNode):
                try:
                    v = self.symbol_table[tree.value]
                except KeyError:
                    print(
                        "{} is not a recognized command or symbol.".format(tree.value)
                    )
                else:
                    self.print_symbol(tree.value, v)
            elif isinstance(tree, IntNode):
                print(tree.value)
            else:
                raise RuntimeError(
                    "unknown node type {}".format(node.__class__.__name__)
                )
        except HERAError as e:
            print("Eval error: " + str(e) + ".")

    def evaluate_node(self, node):
        if isinstance(node, IntNode):
            return node.value
        elif isinstance(node, RegisterNode):
            if node.value == "pc":
                return self.vm.pc
            else:
                return self.vm.get_register(node.value)
        elif isinstance(node, MemoryNode):
            address = self.evaluate_node(node.address)
            return self.vm.access_memory(address)
        elif isinstance(node, SymbolNode):
            try:
                return self.symbol_table[node.value]
            except KeyError:
                raise HERAError("undefined symbol `{}`".format(node.value))
        else:
            raise RuntimeError("unknown node type {}".format(node.__class__.__name__))

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

    def print_symbol(self, k, v):
        if isinstance(v, Label):
            suffix = " (label)"
        elif isinstance(v, DataLabel):
            suffix = " (data label)"
        elif isinstance(v, Constant):
            suffix = " (constant)"
        else:
            suffix = ""
        print("{} = {}".format(k, v) + suffix)

    def print_op(self, index):
        op = self.program[index].original
        prefix = "-> " if index == self.vm.pc else "   "
        print(prefix + "{:0>4x}  {}".format(index, op_to_string(op)), end="")

        # Print all labels pointing to the line.
        labels = self.reverse_labels[index]
        if labels:
            print(" [{}]".format(", ".join(labels)))
        else:
            print()

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


def get_reverse_labels(symbol_table):
    reverse_labels = defaultdict(list)
    for k, v in symbol_table.items():
        if isinstance(v, Label):
            reverse_labels[v].append(k)
    return reverse_labels
