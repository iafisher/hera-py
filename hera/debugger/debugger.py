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
import copy
import readline  # noqa: F401

from hera.data import Label
from hera.vm import VirtualMachine


class Debugger:
    """A class for debugging. External users should generally use the module-level
    `debug` function instead of this class.
    """

    def __init__(self, program):
        self.program = program.code
        self.symbol_table = program.symbol_table
        # A map from instruction numbers (i.e., possible values of the program counter)
        # to human-readable line numbers.
        self.breakpoints = {}
        self.vm = VirtualMachine()
        # How many CALLs without RETURNs?
        self.calls = 0
        # Back-up of the debugger's state, to implement the "undo" command.
        # Set to None when no operations have been performed, and to "undone" when an
        # "undo" has just been executed.
        self.old = None

        for op in program.data:
            self.vm.exec_one(op)

    def save(self):
        self.old = copy.copy(self)
        self.old.symbol_table = self.symbol_table.copy()
        self.old.breakpoints = self.breakpoints.copy()
        self.old.vm = self.vm.copy()

    def get_breakpoints(self):
        return self.breakpoints

    def set_breakpoint(self, b):
        self.breakpoints[b] = self.get_breakpoint_name(b)

    def exec_ops(self, n=-1, *, until=None):
        """Execute `n` real instructions of the program. If `until` is provided, it
        should be a function that returns True when execution should stop. If `n` is not
        provided or set to a negative number, execution continues until the `until`
        function returns True.
        """
        if until is None:
            until = lambda vm: False  # noqa: E731

        while n != 0:
            real_ops = self.get_real_ops()
            for real_op in real_ops:
                if real_op.name == "CALL":
                    self.calls += 1
                elif real_op.name == "RETURN":
                    self.calls -= 1

                self.vm.exec_one(real_op)

            if self.is_finished() or until(self):
                break

            n -= 1

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
            label = self.find_label(b)
            if label is not None:
                return "{} ({})".format(loc, label)

        return loc

    def find_label(self, ino):
        """Find a label, if one exists, corresponding to the instruction number."""
        for symbol, value in self.symbol_table.items():
            if value == ino and isinstance(value, Label):
                return symbol
        return None

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
