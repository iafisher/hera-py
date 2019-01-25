"""The virtual HERA machine.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from .data import State
from .utils import (
    ALSU_OPS,
    ANSI_MAGENTA_BOLD,
    ANSI_RESET,
    BRANCHES,
    DATA_STATEMENTS,
    from_u16,
    print_message_with_location,
    print_register_debug,
    REGISTER_BRANCHES,
    register_to_index,
    to_u16,
    to_u32,
)


class VirtualMachine:
    """An abstract representation of a HERA processor."""

    def __init__(self, state=State()):
        self.state = state
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
        self.dc = self.state.data_start
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

        while program and program[0].name in DATA_STATEMENTS:
            data_statement = program.pop(0)
            self.exec_one(data_statement)

        self.pc = 0
        while not self.halted and self.pc < len(program):
            self.exec_one(program[self.pc])

    def exec_one(self, op):
        """Execute a single operation."""
        self.location = getattr(op.name, "location", None)

        opc = self.pc
        if op.name in BRANCHES:
            self.exec_branch(op)
        elif op.name in ALSU_OPS:
            self.exec_aslu_op(op)
        else:
            handler = getattr(self, "exec_" + op.name)
            handler(*op.args)
        if self.pc == opc:
            self.halted = True

    def exec_branch(self, op):
        name = op.name if op.name in REGISTER_BRANCHES else op.name[:-1]
        should_branch = getattr(self, "should_" + name)()
        if should_branch:
            if op.name in REGISTER_BRANCHES:
                self.pc = self.get_register(op.args[0])
            else:
                self.pc += op.args[0]
        else:
            self.pc += 1

    def exec_aslu_op(self, op):
        args = [self.get_register(a) for a in op.args[1:]]

        calculator = getattr(self, "calculate_" + op.name)

        result = calculator(*args)
        self.store_register(op.args[0], result)
        self.set_zero_and_sign(result)
        self.pc += 1

    def get_register(self, name):
        """Get the contents of the register with the given name."""
        index = register_to_index(name)
        return self.registers[index]

    def store_register(self, target, value):
        """Store the value in the target register (a string)."""
        index = register_to_index(target)
        if index != 0:
            self.registers[index] = value
            if index == 15 and value >= self.state.data_start:
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

    def exec_SETLO(self, target, value):
        if value > 127:
            value -= 256

        self.store_register(target, to_u16(value))
        self.pc += 1

    def exec_SETHI(self, target, value):
        self.store_register(target, (value << 8) + (self.get_register(target) & 0x00FF))
        self.pc += 1

    def calculate_ADD(self, left, right):
        carry = 1 if not self.flag_carry_block and self.flag_carry else 0

        result = (left + right + carry) & 0xFFFF

        self.flag_carry = result < (left + right + carry)
        self.flag_overflow = from_u16(result) != from_u16(left) + from_u16(right)

        return result

    def calculate_SUB(self, left, right):
        borrow = 1 if not self.flag_carry_block and not self.flag_carry else 0

        # to_u16 is necessary because although left and right are necessarily
        # uints, left - right - borrow might not be.
        result = to_u16((left - right - borrow) & 0xFFFF)

        self.flag_carry = left >= right
        self.flag_overflow = (
            from_u16(result) != from_u16(left) - from_u16(right) - borrow
        )

        return result

    def calculate_MUL(self, left, right):
        if self.flag_sign and not self.flag_carry_block:
            # Take the high 16 bits.
            left = to_u32(from_u16(left))
            right = to_u32(from_u16(right))
            result = ((left * right) & 0xFFFF0000) >> 16
        else:
            # Take the low 16 bits.
            result = (left * right) & 0xFFFF

        self.flag_carry = result < left * right
        self.flag_overflow = from_u16(result) != from_u16(left) * from_u16(right)

        return result

    def calculate_AND(self, left, right):
        return left & right

    def calculate_OR(self, left, right):
        return left | right

    def calculate_XOR(self, left, right):
        return left ^ right

    def exec_INC(self, target, value):
        original = self.get_register(target)
        result = (value + original) & 0xFFFF
        self.store_register(target, result)

        self.set_zero_and_sign(result)
        self.flag_overflow = from_u16(result) != from_u16(original) + value
        self.flag_carry = value + original >= 2 ** 16
        self.pc += 1

    def exec_DEC(self, target, value):
        original = self.get_register(target)
        result = to_u16((original - value) & 0xFFFF)
        self.store_register(target, result)

        self.set_zero_and_sign(result)
        self.flag_overflow = from_u16(result) != from_u16(original) - value
        self.flag_carry = original < value
        self.pc += 1

    def calculate_LSL(self, original):
        carry = 1 if self.flag_carry and not self.flag_carry_block else 0
        result = ((original << 1) + carry) & 0xFFFF

        self.flag_carry = original & 0x8000

        return result

    def calculate_LSR(self, original):
        carry = 2 ** 15 if self.flag_carry and not self.flag_carry_block else 0
        result = (original >> 1) + carry

        self.flag_carry = original % 2 == 1

        return result

    def calculate_LSL8(self, original):
        return (original << 8) & 0xFFFF

    def calculate_LSR8(self, original):
        return original >> 8

    def calculate_ASL(self, original):
        carry = 1 if self.flag_carry and not self.flag_carry_block else 0
        result = ((original << 1) + carry) & 0xFFFF

        self.flag_carry = original & 0x8000
        self.flag_overflow = original & 0x8000 and not result & 0x8000

        return result

    def calculate_ASR(self, original):
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

    def exec_SAVEF(self, target):
        value = (
            int(self.flag_sign)
            + 2 * int(self.flag_zero)
            + 4 * int(self.flag_overflow)
            + 8 * int(self.flag_carry)
            + 16 * int(self.flag_carry_block)
        )
        self.store_register(target, value)
        self.pc += 1

    def exec_RSTRF(self, target):
        value = self.get_register(target)
        self.flag_sign = bool(value & 1)
        self.flag_zero = bool(value & 0b10)
        self.flag_overflow = bool(value & 0b100)
        self.flag_carry = bool(value & 0b1000)
        self.flag_carry_block = bool(value & 0b10000)
        self.pc += 1

    def exec_FON(self, value):
        self.flag_sign = self.flag_sign or bool(value & 1)
        self.flag_zero = self.flag_zero or bool(value & 0b10)
        self.flag_overflow = self.flag_overflow or bool(value & 0b100)
        self.flag_carry = self.flag_carry or bool(value & 0b1000)
        self.flag_carry_block = self.flag_carry_block or bool(value & 0b10000)
        self.pc += 1

    def exec_FOFF(self, value):
        self.flag_sign = self.flag_sign and not bool(value & 1)
        self.flag_zero = self.flag_zero and not bool(value & 0b10)
        self.flag_overflow = self.flag_overflow and not bool(value & 0b100)
        self.flag_carry = self.flag_carry and not bool(value & 0b1000)
        self.flag_carry_block = self.flag_carry_block and not bool(value & 0b10000)
        self.pc += 1

    def exec_FSET5(self, value):
        self.flag_sign = bool(value & 1)
        self.flag_zero = bool(value & 0b10)
        self.flag_overflow = bool(value & 0b100)
        self.flag_carry = bool(value & 0b1000)
        self.flag_carry_block = bool(value & 0b10000)
        self.pc += 1

    def exec_FSET4(self, value):
        self.flag_sign = bool(value & 1)
        self.flag_zero = bool(value & 0b10)
        self.flag_overflow = bool(value & 0b100)
        self.flag_carry = bool(value & 0b1000)
        self.pc += 1

    def exec_LOAD(self, target, offset, address):
        result = self.access_memory(self.get_register(address) + offset)
        self.set_zero_and_sign(result)
        self.store_register(target, result)
        self.pc += 1

    def exec_STORE(self, source, offset, address):
        self.assign_memory(
            self.get_register(address) + offset, self.get_register(source)
        )
        self.pc += 1

    def should_BR(self):
        return True

    def should_BL(self):
        return self.flag_sign ^ self.flag_overflow

    def should_BGE(self):
        return not (self.flag_sign ^ self.flag_overflow)

    def should_BLE(self):
        return (self.flag_sign ^ self.flag_overflow) or self.flag_zero

    def should_BG(self):
        return not (self.flag_sign ^ self.flag_overflow) and not self.flag_zero

    def should_BULE(self):
        return not self.flag_carry or self.flag_zero

    def should_BUG(self):
        return self.flag_carry and not self.flag_zero

    def should_BZ(self):
        return self.flag_zero

    def should_BNZ(self):
        return not self.flag_zero

    def should_BC(self):
        return self.flag_carry

    def should_BNC(self):
        return not self.flag_carry

    def should_BS(self):
        return self.flag_sign

    def should_BNS(self):
        return not self.flag_sign

    def should_BV(self):
        return self.flag_overflow

    def should_BNV(self):
        return not self.flag_overflow

    def exec_CALL(self, ra, rb):
        old_pc = self.pc
        self.pc = self.get_register(rb)
        self.store_register(rb, old_pc + 1)
        old_fp = self.get_register("FP")
        self.store_register("FP", self.get_register(ra))
        self.store_register(ra, old_fp)

    # CALL and RETURN do the exact same thing.
    exec_RETURN = exec_CALL

    def exec_SWI(self, i):
        if not self.warned_for_SWI:
            self.print_warning("SWI is a no-op in this simulator", loc=self.location)
            self.warned_for_SWI = True
        self.pc += 1

    def exec_RTI(self):
        if not self.warned_for_RTI:
            self.print_warning("RTI is a no-op in this simulator", loc=self.location)
            self.warned_for_RTI = True
        self.pc += 1

    def exec_INTEGER(self, i):
        self.assign_memory(self.dc, to_u16(i))
        self.dc += 1
        self.pc += 1

    def exec_DSKIP(self, n):
        self.dc += n
        self.pc += 1

    def exec_LP_STRING(self, s):
        self.assign_memory(self.dc, len(s))
        self.dc += 1
        for c in s:
            self.assign_memory(self.dc, ord(c))
            self.dc += 1
        self.pc += 1

    def exec_print_reg(self, target):
        v = self.get_register(target)
        print_register_debug(target, v, to_stderr=False)
        self.pc += 1

    def exec_print(self, target):
        print(target, end="")
        self.pc += 1

    def exec_println(self, target):
        print(target)
        self.pc += 1

    def exec___eval(self, expr):
        # Rudimentary safeguard to make execution of malicious code harder. Users of
        # hera-py should keep in mind that running arbitrary HERA code is no safer than
        # running arbitrary code of any kind.
        if "import" not in expr:
            bytecode = compile(expr, "<string>", "exec")
            exec(bytecode, {}, {"vm": self})

        self.pc += 1

    def print_warning(self, msg, loc):
        if self.state.color:
            msg = ANSI_MAGENTA_BOLD + "Warning" + ANSI_RESET + ": " + msg
        else:
            msg = "Warning: " + msg
        print_message_with_location(msg, loc=loc)
        self.warning_count += 1
