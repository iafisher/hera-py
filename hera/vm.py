"""The virtual HERA machine.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
import functools

from hera.utils import from_uint, to_uint


def ternary_op(f):
    """A decorator for ternary HERA ops. It handles fetching the values of the
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


def binary_op(f):
    """A decorator for binary HERA ops. It handles fetching the value of the
    operand register, storing the result in the target register, setting the
    zero and sign flags, and incrementing the program counter.
    """
    @functools.wraps(f)
    def inner(self, target, original):
        original = self.registers[self.rindex(original)]
        result = f(self, original)
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
            handler = getattr(self, 'exec_' + inst.name.lower())
        except AttributeError:
            raise ValueError(f'unknown instruction "{inst.name}"') from None
        else:
            handler(*inst.args)

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

    def exec_set(self, target, value):
        """Execute the SET pseudo-instruction."""
        self.store_register(target, value)
        self.pc += 1

    def exec_setlo(self, target, value):
        """Execute the SETLO instruction. Note that unlike other op handlers,
        the `value` argument is allowed to be negative. However, it must be in
        the range [-128, 127], as it is only given 8 bits in machine code.
        """
        self.store_register(target, to_uint(value))
        self.pc += 1

    def exec_sethi(self, target, value):
        """Execute the SETHI instruction. `value` must be an integer in the
        range [0, 255].
        """
        self.store_register(target, (value << 8) + (self.getr(target) & 0x00ff))
        self.pc += 1

    @ternary_op
    def exec_add(self, left, right):
        """Execute the ADD instruction."""
        carry = 1 if not self.flag_carry_block and self.flag_carry else 0

        result = (left + right + carry) & 0xffff

        self.flag_carry = result < (left + right + carry)
        self.flag_overflow = (
            from_uint(result) != from_uint(left) + from_uint(right)
        )

        return result

    @ternary_op
    def exec_sub(self, left, right):
        """Execute the SUB instruction."""
        borrow = 1 if not self.flag_carry_block and not self.flag_carry else 0

        # to_uint is necessary because although left and right are necessarily
        # uints, left - right might not be.
        result = to_uint((left - right - borrow) & 0xffff)

        self.flag_overflow = (
            from_uint(result) != from_uint(left) - from_uint(right)
        )
        self.flag_carry = (left > right)

        return result

    @ternary_op
    def exec_mul(self, left, right):
        """Execute the MUL instruction."""
        # TODO

    @ternary_op
    def exec_and(self, left, right):
        """Execute the AND instruction."""
        return left & right

    @ternary_op
    def exec_or(self, left, right):
        """Execute the OR instruction."""
        return left | right

    @ternary_op
    def exec_xor(self, left, right):
        """Execute the XOR instruction."""
        return left ^ right

    def exec_inc(self, target, value):
        """Execute the INC instruction."""
        original = self.getr(target)
        result = (value + original) & 0xffff
        self.store_register(target, result)

        self.set_zero_and_sign(result)
        self.flag_overflow = (from_uint(result) != from_uint(original) + value)
        self.flag_carry = (value + original >= 2**16)
        self.pc += 1

    def exec_dec(self, target, value):
        """Execute the DEC instruction."""
        original = self.getr(target)
        result = to_uint((original - value) & 0xffff)
        self.store_register(target, result)

        self.set_zero_and_sign(result)
        self.flag_overflow = (from_uint(result) != from_uint(original) - value)
        self.flag_carry = (original < value)
        self.pc += 1

    @binary_op
    def exec_lsl(self, original):
        """Execute the LSL instruction."""
        carry = 1 if self.flag_carry and not self.flag_carry_block else 0
        result = ((original << 1) + carry) & 0xffff

        self.flag_carry = original & 0x8000

        return result

    @binary_op
    def exec_lsr(self, original):
        """Execute the LSR instruction."""
        carry = 2**15 if self.flag_carry and not self.flag_carry_block else 0
        result = (original >> 1) + carry

        self.flag_carry = original % 2 == 1

        return result

    @binary_op
    def exec_lsl8(self, original):
        """Execute the LSL8 instruction."""
        return (original << 8) & 0xffff

    @binary_op
    def exec_lsr8(self, original):
        """Execute the LSR8 instruction."""
        return original >> 8

    @binary_op
    def exec_asl(self, original):
        """Execute the ASL instruction."""
        carry = 1 if self.flag_carry and not self.flag_carry_block else 0
        result = ((original << 1) + carry) & 0xffff

        self.flag_carry = original & 0x8000
        self.flag_overflow = (original & 0x8000 and not result & 0x8000)

        return result

    def exec_print_reg(self, target):
        """Execute the print_reg debugging operation."""
        print(f'{target} = {self.registers[self.rindex(target)]}')
        self.pc += 1
