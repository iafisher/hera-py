"""
The definition of all the operations in the HERA language.

Each operation is defined as a class which inherits from `AbstractOperation` or one of
its subclasses. A class for a HERA op typically needs to define only three things:

    - A class-level `P` field that is a tuple of the types of the operations arguments.
      The types are defined in the TYPES FOR `P` FIELD section of this module.

    - A class-level `BITV` field that is a string describing the pattern of the
      operation's binary encoding. See the docstring of `match_bitvector` for a
      description of the pattern format.

    - An `execute` method that takes a `VirtualMachine` object and performs its
      operation on it.

Many subclasses of `AbstractOperation` are provided to ease implementation further, such
as `UnaryOp`, `BinaryOp`, `RegisterBranch`, and `RelativeBranch`.

A class for a HERA pseudo-op typically needs to define only two things:

    - A `P` field, same as regular ops.
    - A `convert` method which converts the pseudo-op into a list of regular operations.

Data operations (e.g., `INTEGER`) should inherit from `DataOperation` and define a `P`
field and `execute` and `assemble` methods. The `assemble` method of a data operation
returns the data, as a `bytes` object, that the operation places into static memory.

Once the operation's class has been defined, make an entry in the `name_to_class`
dictonary in this module. After doing this, the operation should work throughout the
hera-py toolkit (interpreter, debugger, assembler, etc.)!

Author:  Ian Fisher (iafisher@protonmail.com)
Version: July 2019
"""
import json
import sys
from contextlib import suppress

from hera import stdlib
from hera.data import Constant, DataLabel, HERAError, Label, Location, Messages, Token
from hera.utils import format_int, from_u16, print_error, print_warning, to_u16, to_u32
from hera.vm import VirtualMachine


class AbstractOperation:
    """
    The abstract base class for HERA operations. All operation classes should inherit
    from this class.
    """

    # Default value supplied to silence mypy's complaints.
    BITV = ""

    def __init__(self, *args, loc=None):
        self.args = [a.value for a in args]
        self.tokens = list(args)
        # When the preprocessor converts pseudo-ops to real ops, it will set the
        # original field of the real op to the corresponding pseudo-op, for use by the
        # HERA debugger.
        self.original = None

        if isinstance(loc, Location):
            self.loc = loc
        elif hasattr(loc, "location"):
            self.loc = loc.location
        else:
            self.loc = None

    def typecheck(self, symbol_table: "Dict[str, int]") -> Messages:
        """
        Type-check the operation. Subclasses do not generally need to override this
        method, as long as they provide a P class field listing their parameter types.
        """
        messages = Messages()
        if len(self.P) < len(self.tokens):
            msg = "too many args to {} (expected {})".format(self.name, len(self.P))
            messages.err(msg, self.loc)
        elif len(self.P) > len(self.tokens):
            msg = "too few args to {} (expected {})".format(self.name, len(self.P))
            messages.err(msg, self.loc)

        return messages.extend(check_arglist(self.P, self.tokens, symbol_table))

    def convert(self) -> "List[AbstractOperation]":
        """
        Convert the pseudo-operation into a list of real operations. Only pseudo-ops
        need to override this method.
        """
        return [self]

    def assemble(self) -> bytes:
        """
        Assemble the operation into a 16-bit string. Subclasses do not generally need
        to override this method, as long as they provide a BITV class field.
        """
        return substitute_bitvector(self.BITV, self.args)

    @classmethod
    def disassemble(cls, *args):
        """
        Disassemble the integer arguments into an operation. Subclasses do not
        generally need to override this method; it is provided only for the special
        purposes of the INC and DEC classes.
        """
        return cls(*args)

    def execute(self, vm: VirtualMachine) -> None:
        """
        Execute the operation on a virtual machine. Real operations should override
        this method; pseudo-operations should not.
        """
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


# == TYPES FOR `P` FIELD ==
# Use these variables in the `P` field of classes for HERA ops.
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
    """
    Abstract class to simplify implementation of unary operations. Child classes only
    need to implement the calculate method and set the BITV field.
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
        """
        Calculate the result of the unary operation, given a concrete argument.

        The virtual machine is passed in so that the overflow and carry flags can be
        set if necessary.
        """
        raise NotImplementedError


class BinaryOp(AbstractOperation):
    """
    Abstract class to simplify implementation of binary operations. Child classes only
    need to implement the calculate method and set the BITV field.
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
        """
        Calculate the result of the binary operation, given the concrete left and right
        arguments.

        The virtual machine is passed in so that the overflow and carry flags can be
        set if necessary.
        """
        raise NotImplementedError


class Branch(AbstractOperation):
    pass


class RegisterBranch(Branch):
    """
    Abstract class to simplify implementation of register branches. Child classes only
    need to implement the should method and set the BITV field.
    """

    P = (REGISTER_OR_LABEL,)

    def execute(self, vm):
        if self.should(vm):
            vm.pc = vm.load_register(self.args[0])
        else:
            vm.pc += 1

    @staticmethod
    def should(vm):
        """
        Return True if branching should occur, based on the virtual machine's state.
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


class RelativeBranch(Branch):
    """
    Abstract class to simplify implementation of relative branches. Child classes only
    need to implement the should method and set the BITV field.
    """

    P = (I8_OR_LABEL,)

    def execute(self, vm):
        if self.should(vm):
            vm.pc += self.args[0]
        else:
            vm.pc += 1

    @staticmethod
    def should(vm):
        """
        Return True if branching should occur, based on the virtual machine's state.
        """
        raise NotImplementedError


class DebuggingOperation(AbstractOperation):
    pass


class DataOperation(AbstractOperation):
    pass


class SETLO(AbstractOperation):
    """
    SETLO(Rd, v)
      Set register Rd to the sign-extended 8-bit integer v. Sign-extension means that
      Rd will contain the value of v, interpreted as a signed integer, regardless of
      what was in Rd before. In other words, although the operation is called SETLO, it
      affects not just the low 8 bits but also the high 8 bits.

      Note that values of v above 127 are interpreted as negative numbers, so that for
      instance SETLO(R1, 200) results in R1 having a value of -56 (= 200 - 256).

      SETLO does not affect any flags.

      HERA programmers typically use the SET pseudo-operation to assign a value to a
      register, rather than the low-level SETLO operation.
    """

    P = (REGISTER, I8)
    BITV = "1110 AAAA bbbbbbbb"

    def execute(self, vm):
        value = self.args[1]
        if value > 127:
            value -= 256

        vm.store_register(self.args[0], to_u16(value))
        vm.pc += 1


class SETHI(AbstractOperation):
    """
    SETHI(Rd, v)
      Set the high 8 bits of the register Rd to the unsigned 8-bit integer v. SETHI
      is typically used just after a SETLO operation on the same register.

      SETHI does not affect any flags.

      HERA programmers typically use the SET pseudo-operation to assign a value to a
      register, rather than the low-level SETHI operation.
    """

    P = (REGISTER, I8)
    BITV = "1111 AAAA bbbbbbbb"

    def execute(self, vm):
        target, value = self.args
        vm.store_register(target, (value << 8) + (vm.load_register(target) & 0x00FF))
        vm.pc += 1


class SET(AbstractOperation):
    """
    SET(Rd, v)
      Set the register Rd to the signed 16-bit integer v.

      SET cannot be used to set a register to the value of another register; use MOVE
      for that instead.

      SET does not affect any flags.
    """

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
    """
    ADD(Rd, Ra, Rb)
      Compute Ra + Rb and store the result in Rd. If the carry block flag is off, then
      the carry flag will be added to the sum if it is set, i.e. Ra + Rb + 1 will be
      computed instead.

      If the sum exceeds 16 bits, the higher bits are lost. For example, if an ADD
      results in a sum of 0x10067, then 0x0067 will be stored in the destination
      register.

      ADD sets the following flags:
        sign, if the sum was negative
        zero, if the sum was zero
        carry, if the sum exceeded 16 bits
        overflow, if signed integer overflow occurred (i.e., D != A + B under the signed
                  interpretation of the bits of A, B and D)

      HERA programmers will often want to set the carry block flag (using SETCB())
      before performing this operation, to avoid unexpected results.
    """

    BITV = "1010 AAAA BBBB CCCC"

    @staticmethod
    def calculate(vm, left, right):
        carry = 1 if not vm.flag_carry_block and vm.flag_carry else 0

        result = (left + right + carry) & 0xFFFF

        vm.flag_carry = result < (left + right + carry)
        vm.flag_overflow = from_u16(result) != from_u16(left) + from_u16(right)

        return result


class SUB(BinaryOp):
    """
    SUB(Rd, Ra, Rb)
      Compute Ra - Rb and store the result in Rd. If the carry block flag is off, then
      the carry flag will be subtracted from the difference if it is NOT set, i.e.
      Ra - Rb - 1 will be computed instead.

      SUB sets the following flags:
        sign, if the difference was negative
        zero, if the difference was zero
        carry, if there was no need to borrow from the 2^16's place (i.e., A > B,
               interpreting A and B as unsigned)
        overflow, if signed integer overflow occurred (i.e., D != A - B under the signed
                  interpretation of the bits of A, B and D)

      HERA programmers will often want to set the carry block flag (using SETCB())
      before performing this operation, to avoid unexpected results.
    """

    BITV = "1011 AAAA BBBB CCCC"

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
    """
    MUL(Rd, Ra, Rb)
      Compute Ra * Rb and store the result in Rd.

      The behavior of the MUL instruction depends on the values of the flags. If the
      carry-block is on, or if all the flags are off, then it produces the low 16 bits
      of the product. If the carry-block is off and the sign flag is on, then it
      produces the high 16 bits of the product, to facilitate multiplication of large
      numbers. For all other combinations of flags, the behavior of MUL is undefined by
      the HERA specification; in hera-py, MUL will produce the low 16 bits for the other
      combinations of flags.

      MUL sets the following flags:
        sign, if the product was negative
        zero, if the product was zero
        carry, if the product exceeded 16 bits
        carry, if there was no need to borrow from the 2^16's place (i.e., A > B,
               interpreting A and B as unsigned)
        overflow, if signed integer overflow occurs (i.e., D != A * B under the signed
                  interpretation of the bits of A, B and D)

      HERA programmers will often want to set the carry block flag (using SETCB())
      before performing this operation, to avoid unexpected results.
    """

    BITV = "1100 AAAA BBBB CCCC"

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
    """
    AND(Rd, Ra, Rb)
      Compute the bitwise and of Ra and Rb and store the result in Rd. AND's behavior
      does not depend on the flags, but it does set the sign flag when the result is
      negative and the zero flag when the result is zero.
    """

    BITV = "1000 AAAA BBBB CCCC"

    @staticmethod
    def calculate(vm, left, right):
        return left & right


class OR(BinaryOp):
    """
    OR(Rd, Ra, Rb)
      Compute the bitwise or of Ra and Rb and store the result in Rd. OR's behavior does
      not depend on the flags, but it does set the sign flag when the result is negative
      and the zero flag when the result is zero.
    """

    BITV = "1001 AAAA BBBB CCCC"

    @staticmethod
    def calculate(vm, left, right):
        return left | right


class XOR(BinaryOp):
    """
    XOR(Rd, Ra, Rb)
      Compute the bitwise xor of Ra and Rb and store the result in Rd. XOR's behavior
      does not depend on the flags, but it does set the sign flag when the result is
      negative and the zero flag when the result is zero.
    """

    BITV = "1101 AAAA BBBB CCCC"

    @staticmethod
    def calculate(vm, left, right):
        return left ^ right


class INC(AbstractOperation):
    """
    INC(Rd, v)
      Increment the register by v, an integer between 1 and 64 inclusive. INC sets the
      same flags as the equivalent ADD instruction would, but it ignores the carry flag
      when computing its result.
    """

    P = (REGISTER, range(1, 65))
    BITV = "0011 AAAA 10bb bbbb"

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
        # The increment value encoded in the instruction is one less than the actual
        # increment, i.e. INC(R1, 1) is assembled as if it were INC(R1, 0) since the
        # latter is illegal.
        bv = super().assemble()
        return bytes([bv[0], bv[1] - 1])

    @classmethod
    def disassemble(cls, arg0, arg1):
        return cls(arg0, Token(Token.INT, arg1.value + 1))


class DEC(AbstractOperation):
    """
    DEC(Rd, v)
      Decrement the register by v, an integer between 1 and 64 inclusive. DEC sets the
      same flags as the equivalent SUB instruction would, but it ignores the carry flag
      when computing its result.
    """

    P = (REGISTER, range(1, 65))
    BITV = "0011 AAAA 11bb bbbb"

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
        # The decrement value encoded in the instruction is one less than the actual
        # decrement, i.e. DEC(R1, 1) is assembled as if it were DEC(R1, 0) since the
        # latter is illegal.
        bv = super().assemble()
        return bytes([bv[0], bv[1] - 1])

    @classmethod
    def disassemble(cls, arg0, arg1):
        return cls(arg0, Token(Token.INT, arg1.value + 1))


class LSL(UnaryOp):
    """
    LSL(Rd, Rb)
      Shift the value of Rb one bit to the left, and store the result in Rd. If the
      carry-block is off and the carry is set, then the bit 1 is shifted in on the
      right; otherwise 0 is shifted in. The bit shifted out becomes the carry flag.

      LSL sets the sign flag when the result is negative, and the zero flag when the
      result is zero.
    """

    BITV = "0011 AAAA 0000 BBBB"

    @staticmethod
    def calculate(vm, arg):
        carry = 1 if vm.flag_carry and not vm.flag_carry_block else 0
        result = ((arg << 1) + carry) & 0xFFFF

        vm.flag_carry = arg & 0x8000

        return result


class LSR(UnaryOp):
    """
    LSR(Rd, Rb)
      Shift the value of Rb one bit to the right, and store the result in Rd. If the
      carry-block is off and the carry is set, then the bit 1 is shifted in on the
      left; otherwise 0 is shifted in. The bit shifted out becomes the carry flag.

      LSR sets the sign flag when the result is negative, and the zero flag when the
      result is zero.
    """

    BITV = "0011 AAAA 0001 BBBB"

    @staticmethod
    def calculate(vm, arg):
        carry = 2 ** 15 if vm.flag_carry and not vm.flag_carry_block else 0
        result = (arg >> 1) + carry

        vm.flag_carry = arg % 2 == 1

        return result


class LSL8(UnaryOp):
    """
    LSL8(Rd, Rb)
      Shift the value of Rb eight bits to the left, and store the result in Rd.

      LSL8 sets the sign flag when the result is negative, and the zero flag when the
      result is zero.
    """

    BITV = "0011 AAAA 0010 BBBB"

    @staticmethod
    def calculate(vm, arg):
        return (arg << 8) & 0xFFFF


class LSR8(UnaryOp):
    """
    LSR8(Rd, Rb)
      Shift the value of Rb eight bits to the right, and store the result in Rd.

      LSR8 sets the sign flag when the result is negative, and the zero flag when the
      result is zero.
    """

    BITV = "0011 AAAA 0011 BBBB"

    @staticmethod
    def calculate(vm, arg):
        return arg >> 8


class ASL(UnaryOp):
    """
    ASL(Rd, Rb)
      Shift the value of Rb one bit to the left, and store the result in Rd. If the
      carry-block is off and the carry is set, then the bit 1 is shifted in on the
      left; otherwise 0 is shifted in. The bit shifted out becomes the carry flag.

      ASL sets the sign flag when the result is negative, and the zero flag when the
      result is zero.

      The only difference between ASL and LSL is that ASL will additionally set the
      overflow flag to the same value it would receive after executing ADD(Rd, Rb, Rb).
    """

    BITV = "0011 AAAA 0100 BBBB"

    @staticmethod
    def calculate(vm, arg):
        carry = 1 if vm.flag_carry and not vm.flag_carry_block else 0
        result = ((arg << 1) + carry) & 0xFFFF

        vm.flag_carry = arg & 0x8000
        vm.flag_overflow = arg & 0x8000 and not result & 0x8000

        return result


class ASR(UnaryOp):
    """
    ASL(Rd, Rb)
      Shift the value of Rb one bit to the left, and store the result in Rd. If the
      carry-block is off and the carry is set, then the bit 1 is shifted in on the
      left; otherwise 0 is shifted in. The bit shifted out becomes the carry flag.

      ASL sets the sign flag when the result is negative, and the zero flag when the
      result is zero.

      The only difference between ASL and LSL is that ASL will additionally set the
      overflow flag to the same value it would receive after executing ADD(Rd, Rb, Rb).
    """

    BITV = "0011 AAAA 0101 BBBB"

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


class SAVEF(AbstractOperation):
    """
    SAVEF(Rd)
      Save the flags to Rd. The flags are stored in the following bits:

        0: sign
        1: zero
        2: overflow
        3: carry
        4: carry-block

      The higher bits of Rd are set to 0.
    """

    P = (REGISTER,)
    BITV = "0011 AAAA 0111 0000"

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


class RSTRF(AbstractOperation):
    """
    RSTRF(Rd)
      Restore the flags from Rd.

      Normally you should only invoke RSTRF on a register whose contents have previously
      been set by a call to SAVEF.
    """

    P = (REGISTER,)
    BITV = "0011 AAAA 0111 1000"

    def execute(self, vm):
        value = vm.load_register(self.args[0])
        vm.flag_sign = bool(value & 1)
        vm.flag_zero = bool(value & 0b10)
        vm.flag_overflow = bool(value & 0b100)
        vm.flag_carry = bool(value & 0b1000)
        vm.flag_carry_block = bool(value & 0b10000)
        vm.pc += 1


class FON(AbstractOperation):
    """
    FON(v)
      Turn on the flags indicated by the bits of the 5-bit integer v.

        0: sign
        1: zero
        2: overflow
        3: carry
        4: carry-block
    """

    P = (U5,)
    BITV = "0011 000a 0110 aaaa"

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = vm.flag_sign or bool(value & 1)
        vm.flag_zero = vm.flag_zero or bool(value & 0b10)
        vm.flag_overflow = vm.flag_overflow or bool(value & 0b100)
        vm.flag_carry = vm.flag_carry or bool(value & 0b1000)
        vm.flag_carry_block = vm.flag_carry_block or bool(value & 0b10000)
        vm.pc += 1


class FOFF(AbstractOperation):
    """
    FOFF(v)
      Turn off the flags indicated by the bits of the 5-bit integer v. See the docs for
      FON for a list of which bits of v correspond to which flags.
    """

    P = (U5,)
    BITV = "0011 100a 0110 aaaa"

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = vm.flag_sign and not bool(value & 1)
        vm.flag_zero = vm.flag_zero and not bool(value & 0b10)
        vm.flag_overflow = vm.flag_overflow and not bool(value & 0b100)
        vm.flag_carry = vm.flag_carry and not bool(value & 0b1000)
        vm.flag_carry_block = vm.flag_carry_block and not bool(value & 0b10000)
        vm.pc += 1


class FSET5(AbstractOperation):
    """
    FSET5(v)
      Set the flags according to the bits of the 5-bit integer v. See the docs for FON
      for a list of which bits of v correspond to which flags.
    """

    P = (U5,)
    BITV = "0011 010a 0110 aaaa"

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = bool(value & 1)
        vm.flag_zero = bool(value & 0b10)
        vm.flag_overflow = bool(value & 0b100)
        vm.flag_carry = bool(value & 0b1000)
        vm.flag_carry_block = bool(value & 0b10000)
        vm.pc += 1


class FSET4(AbstractOperation):
    """
    FSET4(v)
      Like FSET5, except it does not affect the carry-block flag.
    """

    P = (U4,)
    BITV = "0011 110a 0110 aaaa"

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = bool(value & 1)
        vm.flag_zero = bool(value & 0b10)
        vm.flag_overflow = bool(value & 0b100)
        vm.flag_carry = bool(value & 0b1000)
        vm.pc += 1


class LOAD(AbstractOperation):
    """
    LOAD(Rd, o, Rb)
      Load into Rd the value at memory location Rb + o, where o is a 5-bit unsigned
      integer.

      LOAD sets the sign flag when the value loaded into Rd is negative, and the zero
      flag when it is zero.
    """

    P = (REGISTER, U5, REGISTER)
    BITV = "010b AAAA bbbb CCCC"

    def execute(self, vm):
        target, offset, address = self.args

        result = vm.load_memory(vm.load_register(address) + offset)
        vm.set_zero_and_sign(result)
        vm.store_register(target, result)
        vm.pc += 1


class STORE(AbstractOperation):
    """
    STORE(Rd, o, Rb)
      Store the value in Rd at the memory location Rb + o, where o is a 5-bit unsigned
      integer.

      STORE does not set any flags.
    """

    P = (REGISTER, U5, REGISTER)
    BITV = "011b AAAA bbbb CCCC"

    def execute(self, vm):
        source, offset, address = self.args

        vm.store_memory(vm.load_register(address) + offset, vm.load_register(source))
        vm.pc += 1


class BR(RegisterBranch):
    """
    BR(label)
      Jump unconditionally to the given label.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 0000 0000 AAAA"

    @staticmethod
    def should(vm):
        return True


class BRR(RelativeBranch):
    """
    BRR(n)
      Jump forward or backward n instructions.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 0000 aaaa aaaa"

    def execute(self, vm):
        if self.args[0] != 0:
            vm.pc += self.args[0]
        else:
            vm.halted = True


class BL(RegisterBranch):
    """
    BL(label)
      Jump to the given label if either the sign flag or the overflow flag are on, but
      not if both are.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 0010 0000 AAAA"

    @staticmethod
    def should(vm):
        return vm.flag_sign ^ vm.flag_overflow


class BLR(RelativeBranch):
    """
    BLR(n)
      Jump forward or backward n instructions if either the sign flag or the overflow
      flag are on, but not if both are.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 0010 aaaa aaaa"

    @staticmethod
    def should(vm):
        return vm.flag_sign ^ vm.flag_overflow


class BGE(RegisterBranch):
    """
    BGE(label)
      Jump to the given label if the sign flag or the overflow flag are either both on
      or both off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 0011 0000 AAAA"

    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow)


class BGER(RelativeBranch):
    """
    BGER(n)
      Jump forward or backward n instructions if the sign flag or the overflow flag are
      either both on or both off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 0011 aaaa aaaa"

    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow)


class BLE(RegisterBranch):
    """
    BLE(label)
      Jump to the given label under the same conditions as BL, and also if the zero flag
      is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 0100 0000 AAAA"

    @staticmethod
    def should(vm):
        return (vm.flag_sign ^ vm.flag_overflow) or vm.flag_zero


class BLER(RelativeBranch):
    """
    BLER(n)
      Jump forward or backward n instructions under the same conditions as BL, and also
      if the zero flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 0100 aaaa aaaa"

    @staticmethod
    def should(vm):
        return (vm.flag_sign ^ vm.flag_overflow) or vm.flag_zero


class BG(RegisterBranch):
    """
    BG(label)
      Jump to the given label whenever BLE would not jump.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 0101 0000 AAAA"

    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow) and not vm.flag_zero


class BGR(RelativeBranch):
    """
    BGR(n)
      Jump forward or backward n instructions whenever BLE would not jump.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 0101 aaaa aaaa"

    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow) and not vm.flag_zero


class BULE(RegisterBranch):
    """
    BULE(label)
      Jump to the given label if either the carry flag is off or the zero flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 0110 0000 AAAA"

    @staticmethod
    def should(vm):
        return not vm.flag_carry or vm.flag_zero


class BULER(RelativeBranch):
    """
    BULER(n)
      Jump forward or backward n instructions if either the carry flag is off or the
      zero flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 0110 aaaa aaaa"

    @staticmethod
    def should(vm):
        return not vm.flag_carry or vm.flag_zero


class BUG(RegisterBranch):
    """
    BUG(label)
      Jump to the given label if the carry flag is on and the zero flag is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 0111 0000 AAAA"

    @staticmethod
    def should(vm):
        return vm.flag_carry and not vm.flag_zero


class BUGR(RelativeBranch):
    """
    BUGR(n)
      Jump forward or backward n instructions if the carry flag is on and the zero flag
      is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 0111 aaaa aaaa"

    @staticmethod
    def should(vm):
        return vm.flag_carry and not vm.flag_zero


class BZ(RegisterBranch):
    """
    BZ(label)
      Jump to the given label if the zero flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 1000 0000 AAAA"

    @staticmethod
    def should(vm):
        return vm.flag_zero


class BZR(RelativeBranch):
    """
    BZR(n)
      Jump forward or backward n instructions if the zero flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 1000 aaaa aaaa"

    @staticmethod
    def should(vm):
        return vm.flag_zero


class BNZ(RegisterBranch):
    """
    BNZ(label)
      Jump to the given label if the zero flag is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 1001 0000 AAAA"

    @staticmethod
    def should(vm):
        return not vm.flag_zero


class BNZR(RelativeBranch):
    """
    BNZR(n)
      Jump forward or backward n instructions if the zero flag is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 1001 aaaa aaaa"

    @staticmethod
    def should(vm):
        return not vm.flag_zero


class BC(RegisterBranch):
    """
    BC(label)
      Jump to the given label if the carry flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 1010 0000 AAAA"

    @staticmethod
    def should(vm):
        return vm.flag_carry


class BCR(RelativeBranch):
    """
    BCR(n)
      Jump forward or backward n instructions if the carry flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 1010 aaaa aaaa"

    @staticmethod
    def should(vm):
        return vm.flag_carry


class BNC(RegisterBranch):
    """
    BNC(label)
      Jump to the given label if the carry flag is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 1011 0000 AAAA"

    @staticmethod
    def should(vm):
        return not vm.flag_carry


class BNCR(RelativeBranch):
    """
    BNCR(n)
      Jump forward or backward n instructions if the carry flag is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 1011 aaaa aaaa"

    @staticmethod
    def should(vm):
        return not vm.flag_carry


class BS(RegisterBranch):
    """
    BS(label)
      Jump to the given label if the sign flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 1100 0000 AAAA"

    @staticmethod
    def should(vm):
        return vm.flag_sign


class BSR(RelativeBranch):
    """
    BSR(n)
      Jump forward or backward n instructions if the sign flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 1100 aaaa aaaa"

    @staticmethod
    def should(vm):
        return vm.flag_sign


class BNS(RegisterBranch):
    """
    BNS(label)
      Jump to the given label if the sign flag is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 1101 0000 AAAA"

    @staticmethod
    def should(vm):
        return not vm.flag_sign


class BNSR(RelativeBranch):
    """
    BNSR(n)
      Jump forward or backward n instructions if the sign flag is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 1101 aaaa aaaa"

    @staticmethod
    def should(vm):
        return not vm.flag_sign


class BV(RegisterBranch):
    """
    BV(label)
      Jump to the given label if the overflow flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 1110 0000 AAAA"

    @staticmethod
    def should(vm):
        return vm.flag_overflow


class BVR(RelativeBranch):
    """
    BVR(n)
      Jump forward or backward n instructions if the overflow flag is on.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 1110 aaaa aaaa"

    @staticmethod
    def should(vm):
        return vm.flag_overflow


class BNV(RegisterBranch):
    """
    BNV(label)
      Jump to the given label if the overflow flag is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0001 1111 0000 AAAA"

    @staticmethod
    def should(vm):
        return not vm.flag_overflow


class BNVR(RelativeBranch):
    """
    BNVR(n)
      Jump forward or backward n instructions if the overflow flag is off.

      Run `doc branch` for a detailed explanation of branching instructions.
    """

    BITV = "0000 1111 aaaa aaaa"

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
    """
    CALL(FP_alt, function)
      Call the function. The first argument doesn't have to be FP_alt, but you should
      use FP_alt unless you have a good reason not to.

      Unlike in higher-level languages like Python, function calls in HERA don't have
      explicit argument lists. Instead, the caller passes arguments by either placing
      them in designated registers or on designated locations on the stack. The contract
      of where to put arguments is known as the calling convention. See the HERA manual
      for details.

    CALL(Ra, Rb)
      The general-purpose form of the CALL instruction. See the HERA manual for details.
    """

    P = (REGISTER, REGISTER_OR_LABEL)
    BITV = "0010 0000 AAAA BBBB"

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


class RETURN(CALL_AND_RETURN):
    """
    RETURN(FP_alt, PC_ret)
      Return from a function call. The arguments don't have to be FP_alt and PC_ret, but
      you should use them unless you have a good reason not to.

      Unlike in higher-level languages like Python, function returns in HERA don't have
      explicit return values. Instead, the function returns a value by either placing
      it in a designated register or on a designated location on the stack. See the HERA
      manual for details.

    RETURN(Ra, Rb)
      The general-purpose form of the RETURN instruction. See the HERA manual for
      details.
    """

    P = (REGISTER, REGISTER)
    BITV = "0010 0001 AAAA BBBB"

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


class SWI(AbstractOperation):
    """
    SWI(i)
      Simulate a software interrupt that has the number i, a 4-bit integer. The
      counterpart to this instruction is RTI.
    """

    P = (U4,)
    BITV = "0010 0010 0000 aaaa"


class RTI(AbstractOperation):
    """
    RTI()
      Return from a software interrupt. The counterpart to this instruction is SWI.
    """

    P = ()
    BITV = "0010 0011 0000 0000"


class CMP(AbstractOperation):
    """
    CMP(Ra, Rb)
      Compare the values of Ra and Rb. The branch instructions are named so that they
      do the expected thing when immediately preceded by a CMP instruction, e.g.
      CMP(R1, R2) BLE(somewhere_else) will jump to somewhere_else if R1 <= R2.

      At the machine level, this instruction sets the same flags as would be set for
      subtracting Rb from Ra.
    """

    P = (REGISTER, REGISTER)

    def convert(self):
        return [FON(Token.Int(8)), SUB(Token.R(0), self.tokens[0], self.tokens[1])]


class CON(AbstractOperation):
    """
    CON()
      Turn the carry flag on. See also COFF.
    """

    P = ()

    def convert(self):
        return [FON(Token.Int(8))]


class COFF(AbstractOperation):
    """
    COFF()
      Turn the carry flag off. See also CON.
    """

    P = ()

    def convert(self):
        return [FOFF(Token.Int(8))]


class CBON(AbstractOperation):
    """
    CBON()
      Turn the carry-block flag on. See also CCBOFF.
    """

    P = ()

    def convert(self):
        return [FON(Token.Int(16))]


class CCBOFF(AbstractOperation):
    """
    CCBOFF()
      Turn the carry and carry-block flags off. See also CBON and CON.
    """

    P = ()

    def convert(self):
        return [FOFF(Token.Int(24))]


class MOVE(AbstractOperation):
    """
    MOVE(Ra, Rb)
      Set Ra to the value of Rb. Equivalent to an assignment statement in a higher-level
      language.
    """

    P = (REGISTER, REGISTER)

    def convert(self):
        return [OR(self.tokens[0], self.tokens[1], Token.R(0))]


class SETRF(AbstractOperation):
    """
    SETRF(Rd, v)
      Set Rd to v and set the flags for v + 0.
    """

    P = (REGISTER, I16_OR_LABEL)

    def convert(self):
        return SET(*self.args).convert() + FLAGS(self.tokens[0]).convert()


class FLAGS(AbstractOperation):
    """
    FLAGS(Ra)
      Set the flags for Ra + 0.
    """

    P = (REGISTER,)

    def convert(self):
        return [FOFF(Token.Int(8)), ADD(Token.R(0), self.tokens[0], Token.R(0))]


class HALT(AbstractOperation):
    """
    HALT()
      Stop execution of the program, permanently.
    """

    P = ()

    def convert(self):
        return [BRR(Token.Int(0))]


class NOP(AbstractOperation):
    """
    NOP()
      Do nothing.
    """

    P = ()

    def convert(self):
        return [BRR(Token.Int(1))]


class NEG(AbstractOperation):
    """
    NEG(Rd, Ra)
      Compute the arithmetic negation of Ra and store it in Rd. Flags are set as for
      0 - Ra.
    """

    P = (REGISTER, REGISTER)

    def convert(self):
        return [FON(Token.Int(8)), SUB(self.tokens[0], Token.R(0), self.tokens[1])]


class NOT(AbstractOperation):
    """
    NOT(Rd, Ra)
      Compute the logical bitwise negation of Ra and store it in Rd. The sign flag is
      set if the result is negative, and the zero flag if it is zero; no other flags
      are affected.
    """

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


class OPCODE(AbstractOperation):
    """
    OPCODE(d)
      Interpret the 16-bit integer d as a binary encoding of a HERA instruction, and
      execute that instruction.

      There is no good reason to use this, but if you want you can convert your entire
      program into OPCODE instructions by running

        hera preprocess --obfuscate myprogram.hera
    """

    P = (U16,)

    def typecheck(self, *args, **kwargs):
        messages = super().typecheck(*args, **kwargs)

        try:
            disassemble(self.args[0])
        except HERAError:
            messages.err("not a HERA instruction", self.tokens[0])

        return messages

    def convert(self):
        # We don't need to call .convert() on the return value of disassemble because
        # disassemble never returns a pseudo-op.
        return [disassemble(self.args[0])]


class INTEGER(DataOperation):
    """
    INTEGER(i)
      Place the 16-bit signed integer i into the current data cell.

      INTEGER is a data instruction.
    """

    P = (I16,)

    def execute(self, vm):
        vm.store_memory(vm.dc, to_u16(self.args[0]))
        vm.dc += 1

    def assemble(self):
        return bytes([self.args[0] & 0xFF00, self.args[0] & 0xFF])


class DSKIP(DataOperation):
    """
    DSKIP(n)
      Skip the next n data cells. Typically used to reserve space for a fixed-size
      array.

      DSKIP is a data instruction.
    """

    P = (U16,)

    def execute(self, vm):
        vm.dc += self.args[0]

    def assemble(self):
        return bytes([0] * self.args[0] * 2)


class LP_STRING(DataOperation):
    """
    LP_STRING(s)
      Place the length-prefixed string s into memory at the current data cell, so that
      the first cell holds the string's length and the rest of the cells hold the
      ASCII characters of the string.

      LP_STRING is a data instruction.
    """

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
    """
    CONSTANT(x, d)
      Declare the symbol x to have the value d. x can subsequently be used wherever in
      the program the integer d would have been allowed, e.g. in a SET instruction.
    """

    P = (LABEL_TYPE, I16)

    def convert(self):
        return []


class LABEL(AbstractOperation):
    """
    LABEL(l)
      Designate the next instruction as l. Used so that the next instruction can be the
      target of a branching instruction.
    """

    P = (LABEL_TYPE,)

    def convert(self):
        return []


class DLABEL(DataOperation):
    """
    DLABEL(l)
      Designate the next data cell as l. Used so that instructions like LOAD and STORE
      can refer to data declared in the data segment.

      DLABEL is a data instruction.
    """

    P = (LABEL_TYPE,)

    def convert(self):
        return []


class PRINT_REG(DebuggingOperation):
    """
    print_reg(Ra)
      Print the value of Ra.

      print_reg is a debugging instruction.
    """

    P = (REGISTER,)

    def execute(self, vm):
        v = vm.load_register(self.args[0])
        print("R{} = {}".format(self.args[0], format_int(v)))
        vm.pc += 1


class PRINT(DebuggingOperation):
    """
    print(s)
      Print the string literal, without a newline at the end.

      print is a debugging instruction.
    """

    P = (STRING,)

    def execute(self, vm):
        print(self.args[0], end="")
        vm.pc += 1


class PRINTLN(DebuggingOperation):
    """
    println(s)
      Print the string literal with a newline at the end.

      println is a debugging instruction.
    """

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


def disassemble(v: int) -> AbstractOperation:
    """Disassemble a 16-bit integer into a HERA operation."""
    # Iterating over every HERA class is inefficient but simple.
    for cls in name_to_class.values():
        if cls.BITV != "":
            m = match_bitvector(cls.BITV, v)
            if m is not False and isinstance(m, list):
                return cls.disassemble(*m)

    raise HERAError("bit pattern does not correspond to HERA instruction")


def match_bitvector(pattern: str, v: int) -> "Union[List, bool]":
    """
    Try to match the 16-bit integer `v` against `pattern`. Return a list of extracted
    arguments if `v` matches, or False otherwise.

    `pattern` should be a string of sixteen characters, which may be the digits '0' or
    '1' or Latin letters. The digits are matched against the literal digits in `v`;
    letters are used to extract values. Uppercase letters match integer values and
    lowercase letters match registers. For example, "0000aaaaBBBB1111" would match,
    e.g., 0000 1001 0110 11111, returning

        [Token(Token.INT, 0b1001), Token(Token.REGISTER, 0b0110)]
    """
    s = bin(v)[2:].rjust(16, "0")
    args = []  # type: List[Token]

    pattern = pattern.replace(" ", "")

    # Initialize argument list with the correct types (integers or registers).
    for pattern_bit in pattern:
        if pattern_bit.isalpha():
            index = ord(pattern_bit.lower()) - ord("a")
            while index >= len(args):
                args.append(Token(Token.INT, 0))

            if pattern_bit.isupper():
                args[index] = Token(Token.REGISTER, 0)
            else:
                args[index] = Token(Token.INT, 0)

    # Fill in the argument list with the actual values from the binary data.
    for pattern_bit, real_bit in zip(pattern, s):
        if pattern_bit == "0":
            if real_bit != "0":
                return False
        elif pattern_bit == "1":
            if real_bit != "1":
                return False
        else:
            index = ord(pattern_bit.lower()) - ord("a")
            args[index].value <<= 1
            if real_bit == "1":
                args[index].value += 1

    return args


def substitute_bitvector(pattern: str, args: "List[int]") -> bytes:
    """
    Given a 16-bit pattern and a list of arguments, substitute the arguments into the
    pattern to yield a two-byte machine operation.
    """
    # Make a copy of the arguments as we will be modifying it.
    args = args[:]

    # Remove spaces from the pattern string.
    pattern = pattern.replace(" ", "")

    # Substituting the low byte MUST happen before the high byte, because it pulls the
    # low bits from each argument.
    low_pattern = pattern[8:16]
    low_byte = substitute_half_a_bitvector(low_pattern, args)

    high_pattern = pattern[0:8]
    high_byte = substitute_half_a_bitvector(high_pattern, args)

    return bytes([high_byte, low_byte])


def substitute_half_a_bitvector(pattern: str, args: "List[int]") -> int:
    """
    Helper function for `substitute_bitvector`. Takes an 8-bit pattern and returns a
    single byte.
    """
    ret = 0
    for shift, pattern_bit in enumerate(reversed(pattern)):
        if pattern_bit == "0":
            real_bit = 0
        elif pattern_bit == "1":
            real_bit = 1
        else:
            index = ord(pattern_bit.lower()) - ord("a")
            real_bit = args[index] & 1
            args[index] >>= 1

        ret += real_bit << shift

    return ret


def check_arglist(argtypes, args, symbol_table):
    """
    Check that the values in `args` match the types in `argtypes`, and return a
    `Messages` object with any warnings or errors generated.
    """
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


def check_register(arg) -> "Optional[str]":
    """
    Check that `arg` is a register. Return an error message as a string if it is not.
    """
    if arg.type == Token.REGISTER:
        return None
    else:
        if isinstance(arg.value, str) and arg.value.lower() == "pc":
            return "program counter cannot be accessed or changed directly"
        else:
            return "expected register"


def check_register_or_label(arg, symbol_table: "Dict[str, int]") -> "Optional[str]":
    """
    Check that `arg` is a register or a label. Return an error message as a string if it
    is not.
    """
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


def check_label(arg) -> "Optional[str]":
    """Check that `arg` is a label. Return an error message as a string if it is not."""
    if arg.type == Token.SYMBOL:
        return None
    else:
        return "expected label"


def check_string(arg) -> "Optional[str]":
    """
    Check that `arg` is a string literal. Return an error message as a string if it is
    not.
    """
    if not isinstance(arg, Token) or arg.type != Token.STRING:
        return "expected string literal"
    else:
        return None


def check_in_range(arg, symbol_table, *, lo, hi, labels=False) -> "Optional[str]":
    """
    Check that `arg` is an integer (or a symbol resolving to an integer) within the
    bounds established by `lo` and `hi`.

    If `labels` is True, then `arg` may be a label; otherwise it may only be a constant
    symbol.

    Return an error message as a string if `arg` is not an integer or is not in the
    given bounds.
    """
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
    "OPCODE": OPCODE,
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
