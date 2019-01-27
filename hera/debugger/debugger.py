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

from hera.data import Label
from hera.vm import VirtualMachine


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
        # How many CALLs without RETURNs?
        self.calls = 0

    def get_breakpoints(self):
        return self.breakpoints

    def set_breakpoint(self, b):
        self.breakpoints[b] = self.get_breakpoint_name(b)

    def exec_ops(self, n=None, *, until=None):
        if until is None:
            until = lambda vm: False

        if n is None:
            n = len(self.program)

        for _ in range(n):
            real_ops = self.get_real_ops()
            for real_op in real_ops:
                if real_op.name == "CALL":
                    self.calls += 1
                elif real_op.name == "RETURN":
                    self.calls -= 1

                self.vm.exec_one(real_op)

            if self.is_finished() or until(self):
                break

    def get_labels(self, index):
        return self.reverse_labels[index]

    def reset(self):
        self.vm.reset()

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
            # TODO: This could give wrong results for programs with multiple files.
            for pc, op in enumerate(self.program):
                if op.loc.line == lineno:
                    return pc

            raise ValueError("could not find corresponding line.")

    def get_breakpoint_name(self, b, *, append_label=True):
        """Turn an instruction number into a human-readable location string with the
        file path and line number. More or less the inverse of `resolve_location`.
        """
        op = self.program[b].original or self.program[b]
        path = "<stdin>" if op.loc.path == "-" else op.loc.path
        loc = path + ":" + str(op.loc.line)

        if append_label:
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
