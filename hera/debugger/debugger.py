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
Version: February 2019
"""
import copy
import readline  # noqa: F401
from typing import Dict, List, Optional

from hera.data import Label, Program, Settings
from hera.op import AbstractOperation
from hera.vm import VirtualMachine


class Debugger:
    """A class for debugging. External users should generally use the module-level
    `debug` function instead of this class.
    """

    def __init__(self, program: Program, settings: Settings) -> None:
        self.settings = settings
        self.program = program
        self.symbol_table = program.symbol_table
        # A map from instruction numbers (i.e., possible values of the program counter)
        # to human-readable line numbers.
        self.breakpoints = {}  # type: Dict[int, str]
        self.vm = VirtualMachine()
        # How many CALLs without RETURNs?
        self.calls = 0
        # Back-up of the debugger's state, to implement the "undo" command.
        # Set to None when no operations have been performed, and to "undone" when an
        # "undo" has just been executed.
        self.old = None  # type: Optional[Debugger]

        for data_op in self.program.data:
            data_op.execute(self.vm)

    def save(self) -> None:
        self.old = copy.copy(self)
        self.old.symbol_table = self.program.symbol_table.copy()
        self.old.breakpoints = self.breakpoints.copy()
        self.old.vm = self.vm.copy()

    def get_breakpoints(self) -> Dict[int, str]:
        return self.breakpoints

    def set_breakpoint(self, b: int) -> None:
        self.breakpoints[b] = self.get_breakpoint_name(b)

    def exec_ops(self, n=-1, *, until=None) -> None:
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

                real_op.execute(self.vm)

            if self.is_finished() or until(self):
                break

            n -= 1

    def reset(self) -> None:
        self.vm.reset()

    def get_real_ops(self) -> List[AbstractOperation]:
        """Return all the real ops that correspond to the current original op. See
        module docstring for explanation of terminology.
        """
        original = self.program.code[self.vm.pc].original
        end = self.vm.pc
        while (
            end < len(self.program.code) and self.program.code[end].original == original
        ):
            end += 1

        return self.program.code[self.vm.pc : end]

    def resolve_location(self, b: str) -> int:
        """Resolve a user-supplied location string into an instruction number"""
        try:
            lineno = int(b)
        except ValueError:
            try:
                opno = self.program.symbol_table[b]
                assert isinstance(opno, Label)
                return opno
            except (KeyError, AssertionError):
                raise ValueError("could not locate label `{}`.".format(b)) from None
        else:
            # TODO: This could give wrong results for programs with multiple files.
            for pc, op in enumerate(self.program.code):
                if op.loc.line == lineno:
                    return pc

            raise ValueError("could not find corresponding line.")

    def get_breakpoint_name(self, b: int, *, append_label=True) -> str:
        """Turn an instruction number into a human-readable location string with the
        file path and line number. More or less the inverse of `resolve_location`.
        """
        op = self.program.code[b].original or self.program.code[b]
        path = "<stdin>" if op.loc.path == "-" else op.loc.path
        loc = path + ":" + str(op.loc.line)

        if append_label:
            # Look for a label corresponding to the breakpoint.
            label = self.find_label(b)
            if label is not None:
                return "{} ({})".format(loc, label)

        return loc

    def find_label(self, ino: int) -> Optional[str]:
        """Find a label, if one exists, corresponding to the instruction number."""
        for symbol, value in self.program.symbol_table.items():
            if value == ino and isinstance(value, Label):
                return symbol
        return None

    def is_finished(self) -> bool:
        return self.vm.halted or self.vm.pc >= len(self.program.code)

    def empty(self) -> bool:
        return len(self.program.code) == 0


def reverse_lookup_label(symbol_table: Dict[str, int], value: int) -> Optional[str]:
    """Return the name of the label that maps to `value`, or None if no such label is
    found. Constants and data labels are ignored.
    """
    for k, v in symbol_table.items():
        if value == v and isinstance(v, Label):
            return k
    return None
