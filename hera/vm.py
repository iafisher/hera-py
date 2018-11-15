"""The virtual HERA machine.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
import functools

from .preprocessor import HERA_DATA_START
from .utils import from_u16, to_u16, to_u32


def ternary_op(f):
    """A decorator for ternary HERA ops. It handles fetching the values of the
    left and right registers, storing the result in the target register,
    setting the zero and sign flags, and incrementing the program counter.
    """

    @functools.wraps(f)
    def inner(self, target, left, right):
        left = self.get_register(left)
        right = self.get_register(right)
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
        original = self.get_register(original)
        result = f(self, original)
        self.store_register(target, result)
        self.set_zero_and_sign(result)
        self.pc += 1

    return inner


def branch(f):
    """A decorator for HERA register branching instructions. Implementing
    functions only need to return a boolean indicating whether to branch (True)
    or not (False).
    """

    @functools.wraps(f)
    def inner(self, dest):
        if f(self):
            self.pc = self.get_register(dest)
        else:
            self.pc += 1

    return inner


def relative_branch(f):
    """A decorator for HERA relative branching instructions. Implementing
    functions only need to return a boolean indicating whether to branch (True)
    or not (False).
    """

    @functools.wraps(f)
    def inner(self, offset):
        if f(self):
            self.pc += offset
        else:
            self.pc += 1

    return inner


class VirtualMachine:
    """An abstract representation of a HERA processor."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the machine to its initial state."""
        # Sixteen 16-bit registers. The virtual machine stores integers in
        # their unsigned representation, so the values of self.registers will
        # always be non-negative, although values above 2**15 implicitly
        # represent negative integers under a signed interpretation.
        self.registers = [0] * 16
        # 16-bit program counter
        self.pc = 0
        # Current memory cell for data instructions
        self.dc = HERA_DATA_START
        # Status/control flags
        self.flag_sign = False
        self.flag_zero = False
        self.flag_overflow = False
        self.flag_carry = False
        self.flag_carry_block = False
        # A memory array of 16-bit words. The HERA specification requires 2**16
        # words to be addressable, but we start off with a considerably smaller
        # array and expand it as necessary, to keep the start-up time fast.
        self.memory = [0] * (2 ** 4)

    def exec_one(self, inst):
        """Execute a single instruction."""
        try:
            handler = getattr(self, "exec_" + inst.name.lower())
        except AttributeError:
            raise ValueError('unknown instruction "{}"'.format(inst.name)) from None
        else:
            handler(*inst.args)

    def exec_many(self, program):
        """Execute a program (i.e., a list of instructions), resetting the
        machine's state beforehand.
        """
        self.reset()
        while self.pc < len(program):
            opc = self.pc
            self.exec_one(program[self.pc])
            if opc == self.pc:
                break

    def get_register(self, name):
        """Get the contents of the register with the given name."""
        return self.registers[self.rindex(name)]

    def rindex(self, name):
        """Return the index of the register with the given name in the register
        array.
        """
        name = name.lower()
        if name == "rt":
            return 11
        elif name.startswith("r"):
            return int(name[1:])
        elif name == "fp":
            return 14
        elif name == "sp":
            return 15
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
        self.flag_sign = (value & 0x8000)

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

    def exec_setlo(self, target, value):
        """Execute the SETLO instruction. Note that unlike other op handlers,
        the `value` argument is allowed to be negative. However, it must be in
        the range [-128, 127], as it is only given 8 bits in machine code.
        """
        self.store_register(target, to_u16(value))
        self.pc += 1

    def exec_sethi(self, target, value):
        """Execute the SETHI instruction. `value` must be an integer in the
        range [0, 255].
        """
        self.store_register(target, (value << 8) + (self.get_register(target) & 0x00ff))
        self.pc += 1

    @ternary_op
    def exec_add(self, left, right):
        """Execute the ADD instruction."""
        carry = 1 if not self.flag_carry_block and self.flag_carry else 0

        result = (left + right + carry) & 0xffff

        self.flag_carry = result < (left + right + carry)
        self.flag_overflow = (from_u16(result) != from_u16(left) + from_u16(right))

        return result

    @ternary_op
    def exec_sub(self, left, right):
        """Execute the SUB instruction."""
        borrow = 1 if not self.flag_carry_block and not self.flag_carry else 0

        # to_u16 is necessary because although left and right are necessarily
        # uints, left - right - borrow might not be.
        result = to_u16((left - right - borrow) & 0xffff)

        self.flag_carry = (left >= right)
        self.flag_overflow = (from_u16(result) != from_u16(left) - from_u16(right))

        return result

    @ternary_op
    def exec_mul(self, left, right):
        """Execute the MUL instruction."""
        if self.flag_sign and not self.flag_carry_block:
            # Take the high 16 bits.
            left = to_u32(from_u16(left))
            right = to_u32(from_u16(right))
            result = ((left * right) & 0xffff0000) >> 16
        else:
            # Take the low 16 bits.
            result = (left * right) & 0xffff

        self.flag_carry = result < left * right
        self.flag_overflow = (from_u16(result) != from_u16(left) * from_u16(right))

        return result

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
        original = self.get_register(target)
        result = (value + original) & 0xffff
        self.store_register(target, result)

        self.set_zero_and_sign(result)
        self.flag_overflow = (from_u16(result) != from_u16(original) + value)
        self.flag_carry = (value + original >= 2 ** 16)
        self.pc += 1

    def exec_dec(self, target, value):
        """Execute the DEC instruction."""
        original = self.get_register(target)
        result = to_u16((original - value) & 0xffff)
        self.store_register(target, result)

        self.set_zero_and_sign(result)
        self.flag_overflow = (from_u16(result) != from_u16(original) - value)
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
        carry = 2 ** 15 if self.flag_carry and not self.flag_carry_block else 0
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

    @binary_op
    def exec_asr(self, original):
        """Execute the ASR instruction."""
        # This is a little messy because right shift in Python rounds towards
        # negative infinity (7 >> 1 == -4) but in HERA it rounds towards zero
        # (7 >> 1 == -3).
        if original & 0x8000:
            if original & 0x0001:
                result = ((original >> 1) | 0x8000) + 1
            else:
                result = original >> 1 | 0x8000
        else:
            result = original >> 1

        self.flag_carry = original & 0x0001

        return result

    def exec_savef(self, target):
        """Execute the SAVE instruction."""
        value = (
            int(self.flag_sign)
            + 2
            * int(self.flag_zero)
            + 4
            * int(self.flag_overflow)
            + 8
            * int(self.flag_carry)
            + 16
            * int(self.flag_carry_block)
        )
        self.store_register(target, value)
        self.pc += 1

    def exec_rstrf(self, target):
        """Execute the RSTRF instruction."""
        value = self.get_register(target)
        self.flag_sign = bool(value & 1)
        self.flag_zero = bool(value & 0b10)
        self.flag_overflow = bool(value & 0b100)
        self.flag_carry = bool(value & 0b1000)
        self.flag_carry_block = bool(value & 0b10000)
        self.pc += 1

    def exec_fon(self, value):
        """Execute the FON instruction."""
        self.flag_sign = self.flag_sign or bool(value & 1)
        self.flag_zero = self.flag_zero or bool(value & 0b10)
        self.flag_overflow = self.flag_overflow or bool(value & 0b100)
        self.flag_carry = self.flag_carry or bool(value & 0b1000)
        self.flag_carry_block = self.flag_carry_block or bool(value & 0b10000)
        self.pc += 1

    def exec_foff(self, value):
        """Execute the FOFF instruction."""
        self.flag_sign = self.flag_sign and not bool(value & 1)
        self.flag_zero = self.flag_zero and not bool(value & 0b10)
        self.flag_overflow = self.flag_overflow and not bool(value & 0b100)
        self.flag_carry = self.flag_carry and not bool(value & 0b1000)
        self.flag_carry_block = (self.flag_carry_block and not bool(value & 0b10000))
        self.pc += 1

    def exec_fset5(self, value):
        """Execute the FSET5 instruction."""
        self.flag_sign = bool(value & 1)
        self.flag_zero = bool(value & 0b10)
        self.flag_overflow = bool(value & 0b100)
        self.flag_carry = bool(value & 0b1000)
        self.flag_carry_block = bool(value & 0b10000)
        self.pc += 1

    def exec_fset4(self, value):
        """Execute the FSET4 instruction."""
        self.flag_sign = bool(value & 1)
        self.flag_zero = bool(value & 0b10)
        self.flag_overflow = bool(value & 0b100)
        self.flag_carry = bool(value & 0b1000)
        self.pc += 1

    def exec_load(self, target, offset, address):
        """Execute the LOAD instruction."""
        result = self.access_memory(self.get_register(address) + offset)
        self.set_zero_and_sign(result)
        self.store_register(target, result)
        self.pc += 1

    def exec_store(self, source, offset, address):
        """Execute the STORE instruction."""
        self.assign_memory(
            self.get_register(address) + offset, self.get_register(source)
        )
        self.pc += 1

    def exec_br(self, dest):
        """Execute the BR instruction."""
        self.pc = self.get_register(dest)

    def exec_brr(self, offset):
        """Execute the BRR instruction."""
        self.pc += offset

    @branch
    def exec_bl(self):
        """Execute the BL instruction."""
        return self.flag_sign ^ self.flag_overflow

    @relative_branch
    def exec_blr(self):
        """Execute the BLR instruction."""
        return self.flag_sign ^ self.flag_overflow

    @branch
    def exec_bge(self):
        """Execute the BGE instruction."""
        return not (self.flag_sign ^ self.flag_overflow)

    @relative_branch
    def exec_bger(self):
        """Execute the BGER instruction."""
        return not (self.flag_sign ^ self.flag_overflow)

    @branch
    def exec_ble(self):
        """Execute the BLE instruction."""
        return (self.flag_sign ^ self.flag_overflow) or self.flag_zero

    @relative_branch
    def exec_bler(self):
        """Execute the BLER instruction."""
        return (self.flag_sign ^ self.flag_overflow) or self.flag_zero

    @branch
    def exec_bg(self):
        """Execute the BG instruction."""
        return not (self.flag_sign ^ self.flag_overflow) and not self.flag_zero

    @relative_branch
    def exec_bgr(self):
        """Execute the BGR instruction."""
        return not (self.flag_sign ^ self.flag_overflow) and not self.flag_zero

    @branch
    def exec_bule(self):
        """Execute the BULE instruction."""
        return not self.flag_carry or self.flag_zero

    @relative_branch
    def exec_buler(self):
        """Execute the BULER instruction."""
        return not self.flag_carry or self.flag_zero

    @branch
    def exec_bug(self):
        """Execute the BUG instruction."""
        return self.flag_carry and not self.flag_zero

    @relative_branch
    def exec_bugr(self):
        """Execute the BUGR instruction."""
        return self.flag_carry and not self.flag_zero

    @branch
    def exec_bz(self):
        """Execute the BZ instruction."""
        return self.flag_zero

    @relative_branch
    def exec_bzr(self):
        """Execute the BZR instruction."""
        return self.flag_zero

    @branch
    def exec_bnz(self):
        """Execute the BNZ instruction."""
        return not self.flag_zero

    @relative_branch
    def exec_bnzr(self):
        """Execute the BNZR instruction."""
        return not self.flag_zero

    @branch
    def exec_bc(self):
        """Execute the BC instruction."""
        return self.flag_carry

    @relative_branch
    def exec_bcr(self):
        """Execute the BCR instruction."""
        return self.flag_carry

    @branch
    def exec_bnc(self):
        """Execute the BNC instruction."""
        return not self.flag_carry

    @relative_branch
    def exec_bncr(self):
        """Execute the BNCR instruction."""
        return not self.flag_carry

    @branch
    def exec_bs(self):
        """Execute the BS instruction."""
        return self.flag_sign

    @relative_branch
    def exec_bsr(self):
        """Execute the BSR instruction."""
        return self.flag_sign

    @branch
    def exec_bns(self):
        """Execute the BNS instruction."""
        return not self.flag_sign

    @relative_branch
    def exec_bnsr(self):
        """Execute the BNSR instruction."""
        return not self.flag_sign

    @branch
    def exec_bv(self):
        """Execute the BV instruction."""
        return self.flag_overflow

    @relative_branch
    def exec_bvr(self):
        """Execute the BVR instruction."""
        return self.flag_overflow

    @branch
    def exec_bnv(self):
        """Execute the BNV instruction."""
        return not self.flag_overflow

    @relative_branch
    def exec_bnvr(self):
        """Execute the BNVR instruction."""
        return not self.flag_overflow

    def exec_call(self, ra, rb):
        """Execute the CALL instruction."""
        old_pc = self.pc
        self.pc = self.get_register(rb)
        self.store_register(rb, old_pc + 1)
        old_fp = self.get_register("FP")
        self.store_register("FP", self.get_register(ra))
        self.store_register(ra, old_fp)

    # CALL and RETURN do the exact same thing.
    exec_return = exec_call

    def exec_integer(self, i):
        """Execute the INTEGER data instruction."""
        self.assign_memory(self.dc, to_u16(i))
        self.dc += 1
        self.pc += 1

    def exec_dskip(self, n):
        """Execute the DSKIP data instruction."""
        self.dc += n
        self.pc += 1

    def exec_lp_string(self, s):
        """Execute the LP_STRING data instruction."""
        self.assign_memory(self.dc, len(s))
        self.dc += 1
        for c in s:
            self.assign_memory(self.dc, ord(c))
            self.dc += 1
        self.pc += 1

    def exec_print_reg(self, target):
        """Execute the print_reg debugging operation."""
        print("{} = {}".format(target, self.get_register(target)))
        self.pc += 1
