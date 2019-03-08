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
from typing import Dict, List, Optional

try:
    import readline  # noqa: F401
except ImportError:
    pass

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

    def at_breakpoint(self) -> bool:
        return not self.finished() and self.vm.pc in self.breakpoints

    def next(self, *, step) -> None:
        if self.finished():
            return

        if not step and self.program.code[self.vm.pc].original.name == "CALL":
            calls = self.calls
            # step=True prevents infinite regress.
            self.next(step=True)
            while (
                not self.finished() and not self.at_breakpoint() and self.calls > calls
            ):
                self.next(step=True)
        else:
            for real_op in self.real_ops():
                if real_op.name == "CALL":
                    self.calls += 1
                elif real_op.name == "RETURN":
                    self.calls -= 1

                real_op.execute(self.vm)

    def reset(self) -> None:
        self.vm.reset()

    def op(self, index=None) -> AbstractOperation:
        """Return the original operation at the given index, which defaults to the
        current program counter.
        """
        if index is None:
            index = self.vm.pc
        return self.program.code[index].original

    def real_ops(self) -> List[AbstractOperation]:
        """Return all the real ops that correspond to the current original op. See
        module docstring for explanation of terminology.
        """
        original = self.op()
        end = self.vm.pc
        while end < len(self.program.code) and self.op(end) == original:
            end += 1

        return self.program.code[self.vm.pc : end]

    def resolve_location(self, b: str) -> int:
        """Resolve a user-supplied location string into an instruction number"""
        if b == ".":
            return self.vm.pc

        if ":" in b:
            path, lineno = b.split(":", maxsplit=1)
        else:
            path = self.op().loc.path
            lineno = b

        try:
            lineno_as_int = int(lineno)
        except ValueError:
            try:
                opno = self.program.symbol_table[b]
                assert isinstance(opno, Label)
                return opno
            except (KeyError, AssertionError):
                raise ValueError("could not locate label `{}`.".format(b)) from None
        else:
            for pc, op in enumerate(self.program.code):
                if op.loc.path == path and op.loc.line == lineno_as_int:
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

    def finished(self) -> bool:
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
