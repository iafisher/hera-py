"""The virtual HERA machine.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import copy
from typing import List

from .data import Settings
from .op import AbstractOperation, DataOperation
from .utils import print_warning


class VirtualMachine:
    """An abstract representation of a HERA processor."""

    def __init__(self, settings=Settings()):
        self.settings = settings
        self.reset()

    def reset(self):
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
        # Stack of (call_address, return_address) pairs for CALL/RETURN instructions.
        # Used for warning messages and debugging.
        self.expected_returns = []
        self.halted = False
        # Location object for the current operation
        self.location = None
        # Have warnings been issued for use of SWI and RTI instructions?
        self.warned_for_SWI = False
        self.warned_for_RTI = False
        self.warned_for_overflow = False
        self.warning_count = 0

    def copy(self):
        ret = copy.copy(self)
        ret.registers = self.registers.copy()
        ret.memory = self.memory.copy()
        return ret

    def exec_many(self, program: List[AbstractOperation]) -> None:
        """Execute a program (i.e., a list of operations), resetting the machine's
        state beforehand.
        """
        self.reset()

        for data_op in program.data:
            self.exec_one(data_op)

        while not self.halted and self.pc < len(program.code):
            self.exec_one(program.code[self.pc])

    def exec_one(self, op):
        """Execute a single operation."""
        self.location = op.loc

        opc = self.pc
        try:
            op.execute(self)
        except NotImplementedError:
            self.handle_not_implemented(op.name)

        if self.pc == opc and not isinstance(op, DataOperation):
            self.halted = True

    def handle_not_implemented(self, name):
        if name == "SWI":
            if not self.warned_for_SWI:
                self.warn("SWI is a no-op in this simulator", loc=self.location)
                self.warned_for_SWI = True
            self.pc += 1
        elif name == "RTI":
            if not self.warned_for_RTI:
                self.warn("RTI is a no-op in this simulator", loc=self.location)
                self.warned_for_RTI = True
            self.pc += 1
        else:
            raise RuntimeError("unsupported operation {}".format(name))

    def load_register(self, index):
        """Get the contents of the register with the given index."""
        return self.registers[index]

    def store_register(self, index, value):
        """Store the value in the target register."""
        if index != 0:
            self.registers[index] = value
            if index == 15 and value >= self.settings.data_start:
                if not self.warned_for_overflow:
                    self.warn(
                        "stack has overflowed into data segment", loc=self.location
                    )
                    self.warned_for_overflow = True

    def set_zero_and_sign(self, value):
        """Set the zero and sign flags based on the value."""
        self.flag_zero = value == 0
        self.flag_sign = value & 0x8000

    def load_memory(self, address):
        """Get the value at the given memory address."""
        if address >= len(self.memory):
            return 0
        else:
            return self.memory[address]

    def store_memory(self, address, value):
        """Store a value to a location in memory."""
        # Extend the size of the memory array if necessary.
        if address >= len(self.memory):
            self.memory.extend([0] * (address - len(self.memory) + 1))
        self.memory[address] = value

    def warn(self, msg, loc):
        print_warning(self.settings, msg, loc=loc)
        self.warning_count += 1
