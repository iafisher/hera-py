"""
The HERA debugger.

The shell interface to the debugger is defined in `shell.py`; this module defines the
basic debugging operations that the shell makes use of.

The code in this package makes an important distinction between "real ops" and "original
ops." Original ops are the HERA operations as they appear in the program that the user
wrote. Real ops are the original ops transformed by the preprocessor into something that
the virtual machine can actually run. For example, a single original SET op corresponds
to two real ops, SETLO and SETHI.

Internally, the debugger operates on real ops, but whenever it displays output to the
user, it must be in terms of original ops so that the user is not confused.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import copy

try:
    # On systems that don't have libreadline installed, this import results in an
    # ImportError, which can just be ignored (of course, readline key bindings won't
    # work, but there's nothing we can do about that).
    import readline  # noqa: F401
except ImportError:
    pass

from hera.data import Label, Program, Settings
from hera.op import AbstractOperation
from hera.vm import VirtualMachine


class Debugger:
    """
    A class for debugging. External users should generally use the `debug` function
    in `shell.py` instead of instantiating this class directly.
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
        # Back-up of the debugger's state, to implement the "undo" command. Implicitly
        # defines a linked list that traverses the debugger's entire history. Set to
        # None when no operations have been performed.
        self.old = None  # type: Optional[Debugger]

        # In the future, step-by-step execution of data operations may be supported, but
        # for now they're just executed before interactive debugging starts.
        for data_op in self.program.data:
            data_op.execute(self.vm)

    def save(self) -> None:
        self.old = copy.copy(self)
        self.old.symbol_table = self.program.symbol_table.copy()
        self.old.breakpoints = self.breakpoints.copy()
        self.old.vm = self.vm.copy()

    def get_breakpoints(self) -> "Dict[int, str]":
        """Get the breakpoints dictionary."""
        return self.breakpoints

    def set_breakpoint(self, b: int) -> None:
        """Set a breakpoint at the given instruction number (not line number)."""
        self.breakpoints[b] = self.instruction_number_to_location(b)

    def at_breakpoint(self) -> bool:
        """Return True if the debugger is currently at a breakpoint."""
        return not self.finished() and self.vm.pc in self.breakpoints

    def next(self, *, step: bool) -> None:
        """
        Advance the debugger by one original instruction.

        When `step` is True and the current operation is a CALL, the entire function
        call up to the matching RETURN is executed. When `step` is False, just the CALL
        operation is executed, and the debugger is left on the first operation of the
        body of the function.
        """
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
        """Reset the internal state of the debugger."""
        self.vm.reset()

    def op(self, index=None) -> AbstractOperation:
        """
        Return the original operation at the given index, which defaults to the current
        program counter.
        """
        if index is None:
            index = self.vm.pc
        return self.program.code[index].original

    def real_ops(self) -> "List[AbstractOperation]":
        """
        Return the real operations that correspond to the current original operation.
        """
        original = self.op()
        end = self.vm.pc
        while end < len(self.program.code) and self.op(end) == original:
            end += 1

        return self.program.code[self.vm.pc : end]

    def location_to_instruction_number(self, b: str) -> int:
        """Resolve a user-supplied location string into an instruction number."""
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

    def instruction_number_to_location(self, b: int, *, append_label=True) -> str:
        """
        Turn an instruction number into a human-readable location string with the file
        path and line number.
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

    def find_label(self, ino: int) -> "Optional[str]":
        """Find a label, if one exists, corresponding to the instruction number."""
        for symbol, value in self.program.symbol_table.items():
            if value == ino and isinstance(value, Label):
                return symbol
        return None

    def finished(self) -> bool:
        """Return True if the debugger has finished executing the program."""
        return self.vm.halted or self.vm.pc >= len(self.program.code)

    def empty(self) -> bool:
        """Return True if the debugged program is empty."""
        return len(self.program.code) == 0


def reverse_lookup_label(symbol_table: "Dict[str, int]", value: int) -> "Optional[str]":
    """
    Return the name of the label that maps to `value`, or None if no such label is
    found. Constants and data labels are ignored.
    """
    for k, v in symbol_table.items():
        if value == v and isinstance(v, Label):
            return k
    return None
