"""The definition of all the operations in the HERA language.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import json
import sys
from contextlib import suppress
from typing import Dict, List, Optional

from hera import stdlib
from hera.data import Constant, DataLabel, Label, Location, Messages, Token
from hera.utils import format_int, from_u16, print_error, print_warning, to_u16, to_u32
from hera.vm import VirtualMachine


class AbstractOperation:
    def __init__(self, *args, loc=None):
        self.args = [a.value for a in args]
        self.tokens = list(args)
        if isinstance(loc, Location):
            self.loc = loc
        elif hasattr(loc, "location"):
            self.loc = loc.location
        else:
            self.loc = None
        self.original = None

    def typecheck(self, symbol_table: Dict[str, int]) -> Messages:
        messages = Messages()
        if len(self.P) < len(self.tokens):
            msg = "too many args to {} (expected {})".format(self.name, len(self.P))
            messages.err(msg, self.loc)
        elif len(self.P) > len(self.tokens):
            msg = "too few args to {} (expected {})".format(self.name, len(self.P))
            messages.err(msg, self.loc)

        return messages.extend(check_arglist(self.P, self.tokens, symbol_table))

    def convert(self) -> List["AbstractOperation"]:
        return [self]

    def assemble(self) -> bytes:
        raise NotImplementedError

    def execute(self, vm: VirtualMachine) -> None:
        raise NotImplementedError

    def __getattr__(self, name):
        if name == "name":
            return self.__class__.__name__
        else:
            raise AttributeError(name)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and len(self.tokens) == len(other.tokens)
            and all(a1 == a2 for a1, a2 in zip(self.tokens, other.tokens))
        )

    def __repr__(self):
        return "{}({})".format(self.name, ", ".join(repr(a) for a in self.tokens))

    def __str__(self):
        return "{}({})".format(
            self.name, ", ".join(arg_to_string(a) for a in self.tokens)
        )


def arg_to_string(arg):
    if arg.type == Token.STRING:
        return json.dumps(arg.value)
    elif arg.type == Token.REGISTER:
        return "R" + str(arg.value)
    else:
        return str(arg.value)


REGISTER = "REGISTER"
REGISTER_OR_LABEL = "REGISTER_OR_LABEL"
STRING = "STRING"
LABEL_TYPE = "LABEL_TYPE"
I16 = range(-2 ** 15, 2 ** 16)
I16_OR_LABEL = "I16_OR_LABEL"
U16 = range(2 ** 16)
I8 = range(-2 ** 7, 2 ** 8)
I8_OR_LABEL = "I8_OR_LABEL"
U5 = range(2 ** 5)
U4 = range(2 ** 4)


class UnaryOp(AbstractOperation):
    """Abstract class to simplify implementation of unary operations. Child classes
    only need to implement the calculate method.
    """

    P = (REGISTER, REGISTER)

    def execute(self, vm):
        arg = vm.load_register(self.args[1])
        result = self.calculate(vm, arg)
        vm.set_zero_and_sign(result)
        vm.store_register(self.args[0], result)
        vm.pc += 1

    @staticmethod
    def calculate(vm, arg):
        """Calculate the result of the unary operation, given a concrete argument.

        The virtual machine is passed in so that the overflow and carry flags can be
        set if necessary.
        """
        raise NotImplementedError


class BinaryOp(AbstractOperation):
    """Abstract class to simplify implementation of binary operations. Child classes
    only need to implement the calculate method and set the OPCODE field.
    """

    P = (REGISTER, REGISTER, REGISTER)

    def execute(self, vm):
        left = vm.load_register(self.args[1])
        right = vm.load_register(self.args[2])
        result = self.calculate(vm, left, right)
        vm.set_zero_and_sign(result)
        vm.store_register(self.args[0], result)
        vm.pc += 1

    @staticmethod
    def calculate(vm, left, right):
        """Calculate the result of the binary operation, given the concrete left and
        right arguments.

        The virtual machine is passed in so that the overflow and carry flags can be
        set if necessary.
        """
        raise NotImplementedError

    def assemble(self):
        return bytes(
            [(self.OPCODE << 4) + self.args[0], (self.args[1] << 4) + self.args[2]]
        )


class Branch(AbstractOperation):
    pass


class RegisterBranch(Branch):
    """Abstract class to simplify implementation of register branches. Child classes
    only need to implement the should method and set the OPCODE field.
    """

    P = (REGISTER_OR_LABEL,)

    def execute(self, vm):
        if self.should(vm):
            vm.pc = vm.load_register(self.args[0])
        else:
            vm.pc += 1

    @staticmethod
    def should(vm):
        """Return True if branching should occur, based on the virtual machine's state.
        """
        raise NotImplementedError

    def convert(self):
        if self.tokens[0].type == Token.REGISTER:
            # When the argument to the branch is a concrete register.
            return super().convert()
        else:
            # When the argument to the branch is a label, which has already been
            # substituted for its value.
            lbl = self.args[0]
            return [
                SETLO(Token.R(11), Token.Int(lbl & 0xFF)),
                SETHI(Token.R(11), Token.Int(lbl >> 8)),
                self.__class__(Token.R(11)),
            ]

    def assemble(self):
        return bytes([(0b0001 << 4) + self.OPCODE, self.args[0]])


class RelativeBranch(Branch):
    """Abstract class to simplify implementation of relative branches. Child classes
    only need to implement the should method and set the OPCODE field.
    """

    P = (I8_OR_LABEL,)

    def execute(self, vm):
        if self.should(vm):
            vm.pc += self.args[0]
        else:
            vm.pc += 1

    @staticmethod
    def should(vm):
        """Return True if branching should occur, based on the virtual machine's state.
        """
        raise NotImplementedError

    def assemble(self):
        return bytes([self.OPCODE, self.args[0]])


class DebuggingOperation(AbstractOperation):
    pass


class DataOperation(AbstractOperation):
    pass


class SETLO(AbstractOperation):
    P = (REGISTER, I8)

    def execute(self, vm):
        value = self.args[1]
        if value > 127:
            value -= 256

        vm.store_register(self.args[0], to_u16(value))
        vm.pc += 1

    def assemble(self):
        return bytes([(0b1110 << 4) + self.args[0], self.args[1]])


class SETHI(AbstractOperation):
    P = (REGISTER, I8)

    def execute(self, vm):
        target, value = self.args
        vm.store_register(target, (value << 8) + (vm.load_register(target) & 0x00FF))
        vm.pc += 1

    def assemble(self):
        return bytes([(0b1111 << 4) + self.args[0], self.args[1]])


class SET(AbstractOperation):
    P = (REGISTER, I16_OR_LABEL)

    def convert(self):
        dest = self.tokens[0]
        value = to_u16(self.args[1])
        lo = value & 0xFF
        hi = value >> 8
        return [
            SETLO(dest, Token.Int(lo), loc=self.loc),
            SETHI(dest, Token.Int(hi), loc=self.loc),
        ]


class ADD(BinaryOp):
    OPCODE = 0b1010

    @staticmethod
    def calculate(vm, left, right):
        carry = 1 if not vm.flag_carry_block and vm.flag_carry else 0

        result = (left + right + carry) & 0xFFFF

        vm.flag_carry = result < (left + right + carry)
        vm.flag_overflow = from_u16(result) != from_u16(left) + from_u16(right)

        return result


class SUB(BinaryOp):
    OPCODE = 0b1011

    @staticmethod
    def calculate(vm, left, right):
        borrow = 1 if not vm.flag_carry_block and not vm.flag_carry else 0

        # to_u16 is necessary because although left and right are necessarily
        # uints, left - right - borrow might not be.
        result = to_u16((left - right - borrow) & 0xFFFF)

        vm.flag_carry = left >= right
        vm.flag_overflow = from_u16(result) != from_u16(left) - from_u16(right) - borrow

        return result


class MUL(BinaryOp):
    OPCODE = 0b1100

    @staticmethod
    def calculate(vm, left, right):
        if vm.flag_sign and not vm.flag_carry_block:
            # Take the high 16 bits.
            left = to_u32(from_u16(left))
            right = to_u32(from_u16(right))
            result = ((left * right) & 0xFFFF0000) >> 16
        else:
            # Take the low 16 bits.
            result = (left * right) & 0xFFFF

        vm.flag_carry = result < left * right
        vm.flag_overflow = from_u16(result) != from_u16(left) * from_u16(right)

        return result


class AND(BinaryOp):
    OPCODE = 0b1000

    @staticmethod
    def calculate(vm, left, right):
        return left & right


class OR(BinaryOp):
    OPCODE = 0b1001

    @staticmethod
    def calculate(vm, left, right):
        return left | right


class XOR(BinaryOp):
    OPCODE = 0b1101

    @staticmethod
    def calculate(vm, left, right):
        return left ^ right


class INC(AbstractOperation):
    P = (REGISTER, range(1, 65))

    def execute(self, vm):
        target, value = self.args

        original = vm.load_register(target)
        result = (value + original) & 0xFFFF
        vm.store_register(target, result)

        vm.set_zero_and_sign(result)
        vm.flag_overflow = from_u16(result) != from_u16(original) + value
        vm.flag_carry = value + original >= 2 ** 16
        vm.pc += 1

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], (0b10 << 6) + self.args[1] - 1])


class DEC(AbstractOperation):
    P = (REGISTER, range(1, 65))

    def execute(self, vm):
        target, value = self.args

        original = vm.load_register(target)
        result = to_u16((original - value) & 0xFFFF)
        vm.store_register(target, result)

        vm.set_zero_and_sign(result)
        vm.flag_overflow = from_u16(result) != from_u16(original) - value
        vm.flag_carry = original < value
        vm.pc += 1

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], (0b11 << 6) + self.args[1] - 1])


class LSL(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        carry = 1 if vm.flag_carry and not vm.flag_carry_block else 0
        result = ((arg << 1) + carry) & 0xFFFF

        vm.flag_carry = arg & 0x8000

        return result

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], self.args[1]])


class LSR(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        carry = 2 ** 15 if vm.flag_carry and not vm.flag_carry_block else 0
        result = (arg >> 1) + carry

        vm.flag_carry = arg % 2 == 1

        return result

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], (0b0001 << 4) + self.args[1]])


class LSL8(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        return (arg << 8) & 0xFFFF

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], (0b0010 << 4) + self.args[1]])


class LSR8(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        return arg >> 8

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], (0b0011 << 4) + self.args[1]])


class ASL(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        carry = 1 if vm.flag_carry and not vm.flag_carry_block else 0
        result = ((arg << 1) + carry) & 0xFFFF

        vm.flag_carry = arg & 0x8000
        vm.flag_overflow = arg & 0x8000 and not result & 0x8000

        return result

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], (0b0100 << 4) + self.args[1]])


class ASR(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        # This is a little messy because right shift in Python rounds towards
        # negative infinity (7 >> 1 == -4) but in HERA it rounds towards zero
        # (7 >> 1 == -3).
        if arg & 0x8000:
            if arg & 0x0001:
                result = ((arg >> 1) | 0x8000) + 1
            else:
                result = arg >> 1 | 0x8000
        else:
            result = arg >> 1

        vm.flag_carry = arg & 0x0001

        return result

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], (0b0101 << 4) + self.args[1]])


class SAVEF(AbstractOperation):
    P = (REGISTER,)

    def execute(self, vm):
        value = (
            int(vm.flag_sign)
            + 2 * int(vm.flag_zero)
            + 4 * int(vm.flag_overflow)
            + 8 * int(vm.flag_carry)
            + 16 * int(vm.flag_carry_block)
        )
        vm.store_register(self.args[0], value)
        vm.pc += 1

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], 0b01110000])


class RSTRF(AbstractOperation):
    P = (REGISTER,)

    def execute(self, vm):
        value = vm.load_register(self.args[0])
        vm.flag_sign = bool(value & 1)
        vm.flag_zero = bool(value & 0b10)
        vm.flag_overflow = bool(value & 0b100)
        vm.flag_carry = bool(value & 0b1000)
        vm.flag_carry_block = bool(value & 0b10000)
        vm.pc += 1

    def assemble(self):
        return bytes([(0b0011 << 4) + self.args[0], 0b01111000])


class FON(AbstractOperation):
    P = (U5,)

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = vm.flag_sign or bool(value & 1)
        vm.flag_zero = vm.flag_zero or bool(value & 0b10)
        vm.flag_overflow = vm.flag_overflow or bool(value & 0b100)
        vm.flag_carry = vm.flag_carry or bool(value & 0b1000)
        vm.flag_carry_block = vm.flag_carry_block or bool(value & 0b10000)
        vm.pc += 1

    def assemble(self):
        hi = self.args[0] >> 4
        lo = self.args[0] & 0b1111
        return bytes([0b00110000 + hi, (0b0110 << 4) + lo])


class FOFF(AbstractOperation):
    P = (U5,)

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = vm.flag_sign and not bool(value & 1)
        vm.flag_zero = vm.flag_zero and not bool(value & 0b10)
        vm.flag_overflow = vm.flag_overflow and not bool(value & 0b100)
        vm.flag_carry = vm.flag_carry and not bool(value & 0b1000)
        vm.flag_carry_block = vm.flag_carry_block and not bool(value & 0b10000)
        vm.pc += 1

    def assemble(self):
        hi = self.args[0] >> 4
        lo = self.args[0] & 0b1111
        return bytes([0b00111000 + hi, (0b0110 << 4) + lo])


class FSET5(AbstractOperation):
    P = (U5,)

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = bool(value & 1)
        vm.flag_zero = bool(value & 0b10)
        vm.flag_overflow = bool(value & 0b100)
        vm.flag_carry = bool(value & 0b1000)
        vm.flag_carry_block = bool(value & 0b10000)
        vm.pc += 1

    def assemble(self):
        hi = self.args[0] >> 4
        lo = self.args[0] & 0b1111
        return bytes([0b00110100 + hi, (0b0110 << 4) + lo])


class FSET4(AbstractOperation):
    P = (U4,)

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = bool(value & 1)
        vm.flag_zero = bool(value & 0b10)
        vm.flag_overflow = bool(value & 0b100)
        vm.flag_carry = bool(value & 0b1000)
        vm.pc += 1

    def assemble(self):
        hi = self.args[0] >> 4
        lo = self.args[0] & 0b1111
        return bytes([0b00111100 + hi, (0b0110 << 4) + lo])


class LOAD(AbstractOperation):
    P = (REGISTER, U5, REGISTER)

    def execute(self, vm):
        target, offset, address = self.args

        result = vm.load_memory(vm.load_register(address) + offset)
        vm.set_zero_and_sign(result)
        vm.store_register(target, result)
        vm.pc += 1

    def assemble(self):
        hi = self.args[1] >> 4
        lo = self.args[1] & 0b1111
        return bytes([((0b0100 + hi) << 4) + self.args[0], (lo << 4) + self.args[2]])


class STORE(AbstractOperation):
    P = (REGISTER, U5, REGISTER)

    def execute(self, vm):
        source, offset, address = self.args

        vm.store_memory(vm.load_register(address) + offset, vm.load_register(source))
        vm.pc += 1

    def assemble(self):
        hi = self.args[1] >> 4
        lo = self.args[1] & 0b1111
        return bytes([((0b0110 + hi) << 4) + self.args[0], (lo << 4) + self.args[2]])


class BR(RegisterBranch):
    OPCODE = 0b0000

    @staticmethod
    def should(vm):
        return True


class BRR(RelativeBranch):
    OPCODE = 0b0000

    def execute(self, vm):
        if self.args[0] != 0:
            vm.pc += self.args[0]
        else:
            vm.halted = True


class BL(RegisterBranch):
    OPCODE = 0b0010

    @staticmethod
    def should(vm):
        return vm.flag_sign ^ vm.flag_overflow


class BLR(RelativeBranch):
    OPCODE = 0b0010

    @staticmethod
    def should(vm):
        return vm.flag_sign ^ vm.flag_overflow


class BGE(RegisterBranch):
    OPCODE = 0b0011

    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow)


class BGER(RelativeBranch):
    OPCODE = 0b0011

    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow)


class BLE(RegisterBranch):
    OPCODE = 0b0100

    @staticmethod
    def should(vm):
        return (vm.flag_sign ^ vm.flag_overflow) or vm.flag_zero


class BLER(RelativeBranch):
    OPCODE = 0b0100

    @staticmethod
    def should(vm):
        return (vm.flag_sign ^ vm.flag_overflow) or vm.flag_zero


class BG(RegisterBranch):
    OPCODE = 0b0101

    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow) and not vm.flag_zero


class BGR(RelativeBranch):
    OPCODE = 0b0101

    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow) and not vm.flag_zero


class BULE(RegisterBranch):
    OPCODE = 0b0110

    @staticmethod
    def should(vm):
        return not vm.flag_carry or vm.flag_zero


class BULER(RelativeBranch):
    OPCODE = 0b0110

    @staticmethod
    def should(vm):
        return not vm.flag_carry or vm.flag_zero


class BUG(RegisterBranch):
    OPCODE = 0b0111

    @staticmethod
    def should(vm):
        return vm.flag_carry and not vm.flag_zero


class BUGR(RelativeBranch):
    OPCODE = 0b0111

    @staticmethod
    def should(vm):
        return vm.flag_carry and not vm.flag_zero


class BZ(RegisterBranch):
    OPCODE = 0b1000

    @staticmethod
    def should(vm):
        return vm.flag_zero


class BZR(RelativeBranch):
    OPCODE = 0b1000

    @staticmethod
    def should(vm):
        return vm.flag_zero


class BNZ(RegisterBranch):
    OPCODE = 0b1001

    @staticmethod
    def should(vm):
        return not vm.flag_zero


class BNZR(RelativeBranch):
    OPCODE = 0b1001

    @staticmethod
    def should(vm):
        return not vm.flag_zero


class BC(RegisterBranch):
    OPCODE = 0b1010

    @staticmethod
    def should(vm):
        return vm.flag_carry


class BCR(RelativeBranch):
    OPCODE = 0b1010

    @staticmethod
    def should(vm):
        return vm.flag_carry


class BNC(RegisterBranch):
    OPCODE = 0b1011

    @staticmethod
    def should(vm):
        return not vm.flag_carry


class BNCR(RelativeBranch):
    OPCODE = 0b1011

    @staticmethod
    def should(vm):
        return not vm.flag_carry


class BS(RegisterBranch):
    OPCODE = 0b1100

    @staticmethod
    def should(vm):
        return vm.flag_sign


class BSR(RelativeBranch):
    OPCODE = 0b1100

    @staticmethod
    def should(vm):
        return vm.flag_sign


class BNS(RegisterBranch):
    OPCODE = 0b1101

    @staticmethod
    def should(vm):
        return not vm.flag_sign


class BNSR(RelativeBranch):
    OPCODE = 0b1101

    @staticmethod
    def should(vm):
        return not vm.flag_sign


class BV(RegisterBranch):
    OPCODE = 0b1110

    @staticmethod
    def should(vm):
        return vm.flag_overflow


class BVR(RelativeBranch):
    OPCODE = 0b1110

    @staticmethod
    def should(vm):
        return vm.flag_overflow


class BNV(RegisterBranch):
    OPCODE = 0b1111

    @staticmethod
    def should(vm):
        return not vm.flag_overflow


class BNVR(RelativeBranch):
    OPCODE = 0b1111

    @staticmethod
    def should(vm):
        return not vm.flag_overflow


class CALL_AND_RETURN(Branch):
    P = (REGISTER, REGISTER_OR_LABEL)

    def execute(self, vm):
        ra, rb = self.args

        old_pc = vm.pc
        vm.pc = vm.load_register(rb)
        vm.store_register(rb, old_pc + 1)
        # FP = R14
        old_fp = vm.load_register(14)
        vm.store_register(14, vm.load_register(ra))
        vm.store_register(ra, old_fp)

    def typecheck(self, *args, **kwargs):
        messages = super().typecheck(*args, **kwargs)
        if len(self.tokens) >= 1 and self.tokens[0].type == Token.REGISTER:
            with suppress(ValueError):
                if self.tokens[0].value != 12:
                    msg = "first argument to {} should be R12".format(self.name)
                    messages.warn(msg, self.tokens[0])
        return messages


class CALL(CALL_AND_RETURN):
    P = (REGISTER, REGISTER_OR_LABEL)

    def convert(self):
        if self.tokens[1].type == Token.REGISTER:
            return super().convert()
        else:
            return SET(Token.R(13), self.tokens[1]).convert() + [
                self.__class__(self.tokens[0], Token.R(13))
            ]

    def execute(self, vm):
        # Push a (call_address, return_address) pair onto the debugging call stack.
        vm.expected_returns.append((vm.load_register(self.args[1]), vm.pc + 1))
        super().execute(vm)

    def assemble(self):
        return bytes([0b00100000, (self.args[0] << 4) + self.args[1]])


class RETURN(CALL_AND_RETURN):
    P = (REGISTER, REGISTER)

    def typecheck(self, *args, **kwargs):
        messages = super().typecheck(*args, **kwargs)
        if len(self.tokens) >= 2 and self.tokens[1].type == Token.REGISTER:
            with suppress(ValueError):
                if self.tokens[1].value != 13:
                    messages.warn(
                        "second argument to RETURN should be R13", self.tokens[1]
                    )
        return messages

    def execute(self, vm):
        got = vm.load_register(self.args[1])
        if vm.settings.warn_return_on:
            if vm.expected_returns:
                _, expected = vm.expected_returns.pop()
                if expected != got:
                    msg = "incorrect return address (got {}, expected {})".format(
                        got, expected
                    )
                    print_warning(vm.settings, msg, loc=vm.location)
                    vm.settings.warning_count += 1
            else:
                msg = "incorrect return address (got {}, expected <nothing>)".format(
                    got
                )
                print_warning(vm.settings, msg, loc=vm.location)
                vm.settings.warning_count += 1
        super().execute(vm)

    def assemble(self):
        return bytes([0b00100001, (self.args[0] << 4) + self.args[1]])


class SWI(AbstractOperation):
    P = (U4,)

    def assemble(self):
        return bytes([0b00100010, self.args[0]])


class RTI(AbstractOperation):
    P = ()

    def assemble(self):
        return bytes([0b00100011, 0])


class CMP(AbstractOperation):
    P = (REGISTER, REGISTER)

    def convert(self):
        return [FON(Token.Int(8)), SUB(Token.R(0), self.tokens[0], self.tokens[1])]


class CON(AbstractOperation):
    P = ()

    def convert(self):
        return [FON(Token.Int(8))]


class COFF(AbstractOperation):
    P = ()

    def convert(self):
        return [FOFF(Token.Int(8))]


class CBON(AbstractOperation):
    P = ()

    def convert(self):
        return [FON(Token.Int(16))]


class CCBOFF(AbstractOperation):
    P = ()

    def convert(self):
        return [FOFF(Token.Int(24))]


class MOVE(AbstractOperation):
    P = (REGISTER, REGISTER)

    def convert(self):
        return [OR(self.tokens[0], self.tokens[1], Token.R(0))]


class SETRF(AbstractOperation):
    P = (REGISTER, I16_OR_LABEL)

    def convert(self):
        return SET(*self.args).convert() + FLAGS(self.tokens[0]).convert()


class FLAGS(AbstractOperation):
    P = (REGISTER,)

    def convert(self):
        return [FOFF(Token.Int(8)), ADD(Token.R(0), self.tokens[0], Token.R(0))]


class HALT(AbstractOperation):
    P = ()

    def convert(self):
        return [BRR(Token.Int(0))]


class NOP(AbstractOperation):
    P = ()

    def convert(self):
        return [BRR(Token.Int(1))]


class NEG(AbstractOperation):
    P = (REGISTER, REGISTER)

    def convert(self):
        return [FON(Token.Int(8)), SUB(self.tokens[0], Token.R(0), self.tokens[1])]


class NOT(AbstractOperation):
    P = (REGISTER, REGISTER)

    def typecheck(self, *args, **kwargs):
        messages = super().typecheck(*args, **kwargs)
        if len(self.tokens) == 2 and self.tokens[1].type == Token.REGISTER:
            with suppress(ValueError):
                if self.tokens[1].value == 11:
                    messages.warn("don't use R11 with NOT", self.tokens[1])
        return messages

    def convert(self):
        return [
            SETLO(Token.R(11), Token.Int(0xFF)),
            SETHI(Token.R(11), Token.Int(0xFF)),
            XOR(self.tokens[0], Token.R(11), self.tokens[1]),
        ]


class INTEGER(DataOperation):
    P = (I16,)

    def execute(self, vm):
        vm.store_memory(vm.dc, to_u16(self.args[0]))
        vm.dc += 1

    def assemble(self):
        return bytes([self.args[0] & 0xFF00, self.args[0] & 0xFF])


class DSKIP(DataOperation):
    P = (U16,)

    def execute(self, vm):
        vm.dc += self.args[0]

    def assemble(self):
        return bytes([0] * self.args[0] * 2)


class LP_STRING(DataOperation):
    P = (STRING,)

    def execute(self, vm):
        vm.store_memory(vm.dc, len(self.args[0]))
        vm.dc += 1
        for c in self.args[0]:
            vm.store_memory(vm.dc, ord(c))
            vm.dc += 1

    def assemble(self):
        s = self.args[0]
        length_bytes = [len(s) & 0xFF00, len(s) & 0xFF]
        data_bytes = []
        for c in s:
            data_bytes.append(0)
            data_bytes.append(ord(c))
        return bytes(length_bytes + data_bytes)


class CONSTANT(DataOperation):
    P = (LABEL_TYPE, I16)

    def convert(self):
        return []


class LABEL(AbstractOperation):
    P = (LABEL_TYPE,)

    def convert(self):
        return []


class DLABEL(DataOperation):
    P = (LABEL_TYPE,)

    def convert(self):
        return []


class PRINT_REG(DebuggingOperation):
    P = (REGISTER,)

    def execute(self, vm):
        v = vm.load_register(self.args[0])
        print("R{} = {}".format(self.args[0], format_int(v)))
        vm.pc += 1


class PRINT(DebuggingOperation):
    P = (STRING,)

    def execute(self, vm):
        print(self.args[0], end="")
        vm.pc += 1


class PRINTLN(DebuggingOperation):
    P = (STRING,)

    def execute(self, vm):
        print(self.args[0])
        vm.pc += 1


class __EVAL(DebuggingOperation):
    P = (STRING,)

    def execute(self, vm):
        try:
            eval(self.args[0], {}, {"stdlib": stdlib, "vm": vm})
        except Exception as e:
            print_error(vm.settings, "Python exception: " + str(e), loc=vm.location)
            sys.exit(3)
        vm.pc += 1


def check_arglist(argtypes, args, symbol_table):
    messages = Messages()
    for expected, got in zip(argtypes, args):
        if expected == REGISTER:
            err = check_register(got)
        elif expected == REGISTER_OR_LABEL:
            err = check_register_or_label(got, symbol_table)
        elif expected == LABEL_TYPE:
            err = check_label(got)
        elif expected == STRING:
            err = check_string(got)
        elif expected == I16_OR_LABEL:
            err = check_in_range(
                got, symbol_table, lo=-2 ** 15, hi=2 ** 16, labels=True
            )
        elif expected == I8_OR_LABEL:
            err = check_in_range(got, symbol_table, lo=-2 ** 7, hi=2 ** 8, labels=True)
        elif isinstance(expected, range):
            err = check_in_range(got, symbol_table, lo=expected.start, hi=expected.stop)
        else:
            raise RuntimeError("unknown parameter type {!r}".format(expected))

        if err is not None:
            messages.err(err, got)
    return messages


def check_register(arg) -> Optional[str]:
    if arg.type == Token.REGISTER:
        return None
    else:
        if isinstance(arg.value, str) and arg.value.lower() == "pc":
            return "program counter cannot be accessed or changed directly"
        else:
            return "expected register"


def check_register_or_label(arg, symbol_table: Dict[str, int]) -> Optional[str]:
    if arg.type == Token.REGISTER:
        return None
    elif arg.type == Token.SYMBOL:
        try:
            val = symbol_table[arg.value]
        except KeyError:
            return "undefined symbol"
        else:
            if isinstance(val, Constant):
                return "constant cannot be used as label"
            elif isinstance(val, DataLabel):
                return "data label cannot be used as branch label"
            else:
                return None
    else:
        return "expected register or label"


def check_label(arg) -> Optional[str]:
    if arg.type == Token.SYMBOL:
        return None
    else:
        return "expected label"


def check_string(arg):
    if not isinstance(arg, Token) or arg.type != Token.STRING:
        return "expected string literal"
    else:
        return None


def check_in_range(arg, symbol_table, *, lo, hi, labels=False):
    if arg.type == Token.SYMBOL:
        try:
            arg = Token.Int(symbol_table[arg.value])
        except KeyError:
            return "undefined constant"
        else:
            if not labels and not isinstance(arg.value, Constant):
                return "cannot use label as constant"
            elif labels and isinstance(arg.value, Label):
                return None

    if arg.type != Token.INT:
        return "expected integer"

    if arg.value < lo or arg.value >= hi:
        return "integer must be in range [{}, {})".format(lo, hi)
    else:
        return None


name_to_class = {
    "ADD": ADD,
    "AND": AND,
    "ASL": ASL,
    "ASR": ASR,
    "BC": BC,
    "BCR": BCR,
    "BG": BG,
    "BGR": BGR,
    "BGE": BGE,
    "BGER": BGER,
    "BL": BL,
    "BLR": BLR,
    "BLE": BLE,
    "BLER": BLER,
    "BNC": BNC,
    "BNCR": BNCR,
    "BNS": BNS,
    "BNSR": BNSR,
    "BNV": BNV,
    "BNVR": BNVR,
    "BNZ": BNZ,
    "BNZR": BNZR,
    "BR": BR,
    "BRR": BRR,
    "BS": BS,
    "BSR": BSR,
    "BUG": BUG,
    "BUGR": BUGR,
    "BULE": BULE,
    "BULER": BULER,
    "BV": BV,
    "BVR": BVR,
    "BZ": BZ,
    "BZR": BZR,
    "CALL": CALL,
    "CBON": CBON,
    "CCBOFF": CCBOFF,
    "CMP": CMP,
    "COFF": COFF,
    "CON": CON,
    "CONSTANT": CONSTANT,
    "DEC": DEC,
    "DLABEL": DLABEL,
    "DSKIP": DSKIP,
    "FLAGS": FLAGS,
    "FOFF": FOFF,
    "FON": FON,
    "FSET4": FSET4,
    "FSET5": FSET5,
    "HALT": HALT,
    "INC": INC,
    "INTEGER": INTEGER,
    "LABEL": LABEL,
    "LOAD": LOAD,
    "LP_STRING": LP_STRING,
    "LSL": LSL,
    "LSL8": LSL8,
    "LSR": LSR,
    "LSR8": LSR8,
    "MOVE": MOVE,
    "MUL": MUL,
    "NEG": NEG,
    "NOP": NOP,
    "NOT": NOT,
    "OR": OR,
    "print": PRINT,
    "println": PRINTLN,
    "print_reg": PRINT_REG,
    "RETURN": RETURN,
    "RSTRF": RSTRF,
    "RTI": RTI,
    "SAVEF": SAVEF,
    "SET": SET,
    "SETHI": SETHI,
    "SETLO": SETLO,
    "SETRF": SETRF,
    "STORE": STORE,
    "SUB": SUB,
    "SWI": SWI,
    "TIGER_STRING": LP_STRING,
    "XOR": XOR,
    "__eval": __EVAL,
}
