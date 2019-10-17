"""
The virtual HERA machine.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import copy
import sys

from .data import Program, Settings
from .utils import print_warning


class VirtualMachine:
    """
    An abstract representation of a HERA processor.

    This class defines the state of a HERA processor and some utility functions for
    manipulating it, but the HERA language itself is defined in `hera/op.py`.
    """

    def __init__(self, settings=Settings()) -> None:
        self.settings = settings
        self.reset()

    def reset(self) -> None:
        """Reset the machine to its initial state."""
        # Sixteen 16-bit registers. The virtual machine stores integers in their
        # unsigned representation, so the values of self.registers will always be
        # non-negative, although values above 2**15 implicitly represent negative
        # integers under a signed interpretation.
        self.registers = [0] * 16
        # 16-bit program counter
        self.pc = 0
        # Current memory cell for data instructions
        self.dc = self.settings.data_start
        # Status/control flags
        self.flag_sign = False
        self.flag_zero = False
        self.flag_overflow = False
        self.flag_carry = False
        self.flag_carry_block = False
        # A memory array of 16-bit words. The HERA specification requires 2**16 words
        # to be addressable, but we start off with a considerably smaller array and
        # expand it as necessary, to keep the start-up time fast.
        self.memory = [0] * (2 ** 4)
        # Used by some Tiger standard library functions for rudimentary IO.
        self.input_buffer = ""
        self.input_pos = 0
        # Stack of (call_address, return_address) pairs for CALL/RETURN instructions.
        # Used for warning messages and debugging.
        self.expected_returns = []  # type: List[Tuple[int, int]]
        # Special flag set by the HALT operation.
        self.halted = False
        # Location object for the current operation
        self.location = None
        # Number of operations that have been executed - used for throttling.
        self.op_count = 0
        # Have warnings been issued for use of SWI and RTI instructions?
        self.warned_for_SWI = False
        self.warned_for_RTI = False
        self.warned_for_overflow = False
        self.warning_count = 0

        # Initialize registers according to --init flag.
        for dest, val in self.settings.init:
            self.registers[dest] = val

    def copy(self) -> "VirtualMachine":
        """Return a copy of the virtual machine."""
        ret = copy.copy(self)
        ret.registers = self.registers.copy()
        ret.memory = self.memory.copy()
        return ret

    def run(self, program: Program) -> None:
        """Execute a program, resetting the machine's state beforehand."""
        self.reset()

        for data_op in program.data:
            data_op.execute(self)

        # This loop is performance-critical, so instead of having a single loop that
        # always does the throttle-checking, we check beforehand if throttling is turned
        # on, to avoid the performance penalty in the (normal) case where throttling is
        # off.
        if self.settings.throttle is False:
            while not self.halted and self.pc < len(program.code):
                op = program.code[self.pc]
                self.location = op.loc
                op.execute(self)
        else:
            while (
                not self.halted
                and self.pc < len(program.code)
                and self.op_count < self.settings.throttle
            ):
                op = program.code[self.pc]
                self.location = op.loc
                op.execute(self)
                self.op_count += 1

    def load_register(self, index: int) -> int:
        """Get the contents of the register with the given index."""
        return self.registers[index]

    def store_register(self, index: int, value: int) -> None:
        """Store the value in the target register."""
        if index != 0:
            self.registers[index] = value
            if index == 15 and value >= self.settings.data_start:
                if not self.warned_for_overflow:
                    self.warn(
                        "stack has overflowed into data segment", loc=self.location
                    )
                    self.warned_for_overflow = True

    def set_zero_and_sign(self, value: int) -> None:
        """Set the zero and sign flags based on the value."""
        self.flag_zero = value == 0
        self.flag_sign = bool(value & 0x8000)

    def load_memory(self, address: int) -> int:
        """Get the value at the given memory address."""
        if address >= len(self.memory):
            return 0
        else:
            return self.memory[address]

    def store_memory(self, address: int, value: int) -> None:
        """Store a value to a location in memory."""
        # Extend the size of the memory array if necessary.
        if address >= len(self.memory):
            self.memory.extend([0] * (address - len(self.memory) + 1))
        self.memory[address] = value

    def readline(self) -> None:
        """Read a line from standard input."""
        self.input_buffer = sys.stdin.readline().rstrip("\n")

    def warn(self, msg: str, loc) -> None:
        """Print a warning message."""
        print_warning(self.settings, msg, loc=loc)
        self.warning_count += 1
