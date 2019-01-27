"""The virtual HERA machine.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from .data import Settings
from .utils import (
    ANSI_MAGENTA_BOLD,
    ANSI_RESET,
    DATA_STATEMENTS,
    print_message_with_location,
    register_to_index,
)


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
        self.halted = False
        # Location object for the current operation
        self.location = None
        # Have warnings been issued for use of SWI and RTI instructions?
        self.warned_for_SWI = False
        self.warned_for_RTI = False
        self.warned_for_overflow = False
        self.warning_count = 0

    def exec_many(self, program):
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
        if self.pc == opc and op.name not in DATA_STATEMENTS:
            self.halted = True

    def handle_not_implemented(self, name):
        if name == "SWI":
            if not self.warned_for_SWI:
                self.print_warning(
                    "SWI is a no-op in this simulator", loc=self.location
                )
                self.warned_for_SWI = True
            self.pc += 1
        elif name == "RTI":
            if not self.warned_for_RTI:
                self.print_warning(
                    "RTI is a no-op in this simulator", loc=self.location
                )
                self.warned_for_RTI = True
            self.pc += 1
        else:
            raise RuntimeError("unsupported operation {}".format(name))

    def get_register(self, name):
        """Get the contents of the register with the given name."""
        # TODO: get_register but access_memory, store_register but assign_memory
        index = register_to_index(name)
        return self.registers[index]

    def store_register(self, target, value):
        """Store the value in the target register (a string)."""
        index = register_to_index(target)
        if index != 0:
            self.registers[index] = value
            if index == 15 and value >= self.settings.data_start:
                if not self.warned_for_overflow:
                    self.print_warning(
                        "stack has overflowed into data segment", loc=self.location
                    )
                    self.warned_for_overflow = True

    def set_zero_and_sign(self, value):
        """Set the zero and sign flags based on the value."""
        self.flag_zero = value == 0
        self.flag_sign = value & 0x8000

    def assign_memory(self, address, value):
        """Assign a value to a location in memory."""
        # Extend the size of the memory array if necessary.
        if address >= len(self.memory):
            self.memory.extend([0] * (address - len(self.memory) + 1))
        self.memory[address] = value

    def access_memory(self, address):
        """Access a value in memory."""
        if address >= len(self.memory):
            return 0
        else:
            return self.memory[address]

    def print_warning(self, msg, loc):
        if self.settings.color:
            msg = ANSI_MAGENTA_BOLD + "Warning" + ANSI_RESET + ": " + msg
        else:
            msg = "Warning: " + msg
        print_message_with_location(msg, loc=loc)
        self.warning_count += 1
