"""The virtual HERA machine.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
import functools

from hera.utils import from_uint, to_uint


def ternary_op(f):
    """A decorator for ternary HERA ops that handles fetching the values of the
    left and right registers, storing the result in the target register,
    setting the zero and sign flags, and incrementing the program counter.
    """
    @functools.wraps(f)
    def inner(self, target, left, right):
        left = self.registers[self.rindex(left)]
        right = self.registers[self.rindex(right)]
        result = f(self, left, right)
        self.store_register(target, result)
        self.set_zero_and_sign(result)
        self.pc += 1
    return inner


class VirtualMachine:
    """An abstract representation of a HERA processor."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the machine to its initial state."""
        # Sixteen 16-bit registers. The virtual machine stores integers in their
        # unsigned representation, so the values of self.registers will always
        # be non-negative, although values above 2**15 implicitly represent
        # negative integers under a signed interpretation.
        self.registers = [0] * 16
        # 16-bit program counter
        self.pc = 0
        # Status/control flags
        self.flag_sign = False
        self.flag_zero = False
        self.flag_overflow = False
        self.flag_carry = False
        self.flag_carry_block = False
        # A memory array of 16-bit words. The HERA specification requires 2**16
        # words to be addressable, but we start off with a considerably smaller
        # array and expand it as necessary, to keep the start-up time fast.
        self.memory = [0] * (2**4)

    def exec_one(self, inst):
        """Execute a single instruction."""
        try:
            handler = self.imap[inst.name]
        except KeyError:
            raise ValueError(f'unknown instruction "{inst.name}"') from None
        else:
            handler(self, *inst.args)

    def exec_many(self, program):
        """Execute a program (i.e., a list of instructions), resetting the
        machine's state beforehand.
        """
        self.reset()
        while self.pc < len(program):
            self.exec_one(program[self.pc])

    def getr(self, name):
        """Get the contents of the register with the given name."""
        return self.registers[self.rindex(name)]

    def rindex(self, name):
        """Return the index of the register with the given name in the register
        array.
        """
        if name.startswith('R'):
            return int(name[1:])
        else:
            raise KeyError(name)

    def store_register(self, target, value):
        """Store the value in the target register (a string)."""
        index = self.rindex(target)
        if index != 0:
            self.registers[index] = value

    def set_zero_and_sign(self, value):
        """Set the zero and sign flags based on the value."""
        self.flag_zero = (value == 0)
        self.flag_sign = (value >= 2**15)

    @ternary_op
    def exec_add(self, left, right):
        """Execute the ADD instruction."""
        carry = 1 if not self.flag_carry_block and self.flag_carry else 0

        result = (left + right + carry) % 2**16

        self.flag_carry = result < (left + right + carry)
        self.flag_overflow = (
            (left < 2**15 and right < 2**15 and result >= 2**15) or
            (left >= 2**15 and right >= 2**15 and result < 2**15)
        )

        return result

    @ternary_op
    def exec_sub(self, left, right):
        """Execute the SUB instruction."""
        borrow = 1 if not self.flag_carry_block and not self.flag_carry else 0

        # to_uint is necessary because although left and right are necessarily
        # uints, left - right might not be.
        result = to_uint((left - right - borrow) % 2**16)

        self.flag_overflow = (
            from_uint(result) != from_uint(left) - from_uint(right)
        )
        self.flag_carry = (left > right)

        return result

    @ternary_op
    def exec_and(self, left, right):
        """Execute the AND instruction."""
        return left & right


    @ternary_op
    def exec_or(self, left, right):
        """Execute the OR instruction."""
        return left | right

    # A mapping from instruction names to handler functions.
    imap = {
        'ADD': exec_add,
        'AND': exec_and,
        'OR': exec_or,
        'SUB': exec_sub,
    }
