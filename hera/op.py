import json
from contextlib import suppress
from typing import Dict, List, Optional, Tuple

from hera.data import Constant, DataLabel, Location, Messages, Op, Token
from hera.utils import (
    format_int,
    from_u16,
    is_register,
    is_symbol,
    register_to_index,
    to_u16,
    to_u32,
)


class Operation:
    # TODO: Name of this class is confusingly similar to hera.data.Op

    def __init__(self, *args, loc=None):
        self.args = list(args)
        if isinstance(loc, Location):
            self.loc = loc
        elif hasattr(loc, "location"):
            self.loc = loc.location
        else:
            self.loc = None
        self.original = None

    def typecheck(self, symbol_table: Dict[str, int]) -> Messages:
        messages = Messages()
        if len(self.P) < len(self.args):
            msg = "too many args to {} (expected {})".format(self.name, len(self.P))
            messages.err(msg, self.loc)
        elif len(self.P) > len(self.args):
            msg = "too few args to {} (expected {})".format(self.name, len(self.P))
            messages.err(msg, self.loc)

        return messages.extend(check_arglist(self.P, self.args, symbol_table))

    def convert(self) -> List["Operation"]:
        return [self]

    def assemble(self):
        raise NotImplementedError

    def execute(self, vm) -> None:
        raise NotImplementedError

    def __getattr__(self, name):
        if name == "name":
            return self.__class__.__name__
        else:
            raise AttributeError(name)

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and len(self.args) == len(other.args)
            and all(a1 == a2 for a1, a2 in zip(self.args, other.args))
        )

    def __repr__(self):
        return "{}({})".format(self.name, ", ".join(repr(a) for a in self.args))

    def __str__(self):
        return "{}({})".format(
            self.name, ", ".join(arg_to_string(a) for a in self.args)
        )


def arg_to_string(arg):
    if isinstance(arg, Token) and arg.type == "STRING":
        return json.dumps(arg)
    else:
        return str(arg)


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


class UnaryOp(Operation):
    """Abstract class to simplify implementation of unary operations. Child classes
    only need to implement the calculate method.
    """

    P = (REGISTER, REGISTER)

    def execute(self, vm):
        arg = vm.get_register(self.args[1])
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


class BinaryOp(Operation):
    """Abstract class to simplify implementation of binary operations. Child classes
    only need to implement the calculate method.
    """

    P = (REGISTER, REGISTER, REGISTER)

    def execute(self, vm):
        left = vm.get_register(self.args[1])
        right = vm.get_register(self.args[2])
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


class RegisterBranch(Operation):
    """Abstract class to simplify implementation of register branches. Child classes
    only need to implement the should method.
    """

    P = (REGISTER_OR_LABEL,)

    def execute(self, vm):
        if self.should(vm):
            vm.pc = vm.get_register(self.args[0])
        else:
            vm.pc += 1

    @staticmethod
    def should(vm):
        """Return True if branching should occur, based on the virtual machine's state.
        """
        raise NotImplementedError

    def convert(self):
        if isinstance(self.args[0], int):
            # When the argument to the branch is a label, which has already been
            # substituted for its value.
            lbl = self.args[0]
            return [
                SETLO("R11", lbl & 0xFF),
                SETHI("R11", lbl >> 8),
                self.__class__("R11"),
            ]
        else:
            # When the argument to the branch is a concrete register.
            return super().convert()


class RelativeBranch(Operation):
    """Abstract class to simplify implementation of relative branches. Child classes
    only need to implement the should method.
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


class SETLO(Operation):
    P = (REGISTER, I8)

    def execute(self, vm):
        value = self.args[1]
        if value > 127:
            value -= 256

        vm.store_register(self.args[0], to_u16(value))
        vm.pc += 1


class SETHI(Operation):
    P = (REGISTER, I8)

    def execute(self, vm):
        target, value = self.args
        vm.store_register(target, (value << 8) + (vm.get_register(target) & 0x00FF))
        vm.pc += 1


class SET(Operation):
    P = (REGISTER, I16_OR_LABEL)

    def convert(self):
        dest = self.args[0]
        value = to_u16(self.args[1])
        lo = value & 0xFF
        hi = value >> 8
        return [SETLO(dest, lo, loc=self.loc), SETHI(dest, hi, loc=self.loc)]


class ADD(BinaryOp):
    @staticmethod
    def calculate(vm, left, right):
        carry = 1 if not vm.flag_carry_block and vm.flag_carry else 0

        result = (left + right + carry) & 0xFFFF

        vm.flag_carry = result < (left + right + carry)
        vm.flag_overflow = from_u16(result) != from_u16(left) + from_u16(right)

        return result


class SUB(BinaryOp):
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
    @staticmethod
    def calculate(vm, left, right):
        return left & right


class OR(BinaryOp):
    @staticmethod
    def calculate(vm, left, right):
        return left | right


class XOR(BinaryOp):
    @staticmethod
    def calculate(vm, left, right):
        return left ^ right


class INC(Operation):
    P = (REGISTER, range(1, 65))

    def execute(self, vm):
        target, value = self.args

        original = vm.get_register(target)
        result = (value + original) & 0xFFFF
        vm.store_register(target, result)

        vm.set_zero_and_sign(result)
        vm.flag_overflow = from_u16(result) != from_u16(original) + value
        vm.flag_carry = value + original >= 2 ** 16
        vm.pc += 1


class DEC(Operation):
    P = (REGISTER, range(1, 65))

    def execute(self, vm):
        target, value = self.args

        original = vm.get_register(target)
        result = to_u16((original - value) & 0xFFFF)
        vm.store_register(target, result)

        vm.set_zero_and_sign(result)
        vm.flag_overflow = from_u16(result) != from_u16(original) - value
        vm.flag_carry = original < value
        vm.pc += 1


class LSL(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        carry = 1 if vm.flag_carry and not vm.flag_carry_block else 0
        result = ((arg << 1) + carry) & 0xFFFF

        vm.flag_carry = arg & 0x8000

        return result


class LSR(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        carry = 2 ** 15 if vm.flag_carry and not vm.flag_carry_block else 0
        result = (arg >> 1) + carry

        vm.flag_carry = arg % 2 == 1

        return result


class LSL8(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        return (arg << 8) & 0xFFFF


class LSR8(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        return arg >> 8


class ASL(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        carry = 1 if vm.flag_carry and not vm.flag_carry_block else 0
        result = ((arg << 1) + carry) & 0xFFFF

        vm.flag_carry = arg & 0x8000
        vm.flag_overflow = arg & 0x8000 and not result & 0x8000

        return result


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


class SAVEF(Operation):
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


class RSTRF(Operation):
    P = (REGISTER,)

    def execute(self, vm):
        value = vm.get_register(self.args[0])
        vm.flag_sign = bool(value & 1)
        vm.flag_zero = bool(value & 0b10)
        vm.flag_overflow = bool(value & 0b100)
        vm.flag_carry = bool(value & 0b1000)
        vm.flag_carry_block = bool(value & 0b10000)
        vm.pc += 1


class FON(Operation):
    P = (U5,)

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = vm.flag_sign or bool(value & 1)
        vm.flag_zero = vm.flag_zero or bool(value & 0b10)
        vm.flag_overflow = vm.flag_overflow or bool(value & 0b100)
        vm.flag_carry = vm.flag_carry or bool(value & 0b1000)
        vm.flag_carry_block = vm.flag_carry_block or bool(value & 0b10000)
        vm.pc += 1


class FOFF(Operation):
    P = (U5,)

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = vm.flag_sign and not bool(value & 1)
        vm.flag_zero = vm.flag_zero and not bool(value & 0b10)
        vm.flag_overflow = vm.flag_overflow and not bool(value & 0b100)
        vm.flag_carry = vm.flag_carry and not bool(value & 0b1000)
        vm.flag_carry_block = vm.flag_carry_block and not bool(value & 0b10000)
        vm.pc += 1


class FSET5(Operation):
    P = (U5,)

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = bool(value & 1)
        vm.flag_zero = bool(value & 0b10)
        vm.flag_overflow = bool(value & 0b100)
        vm.flag_carry = bool(value & 0b1000)
        vm.flag_carry_block = bool(value & 0b10000)
        vm.pc += 1


class FSET4(Operation):
    P = (U4,)

    def execute(self, vm):
        value = self.args[0]
        vm.flag_sign = bool(value & 1)
        vm.flag_zero = bool(value & 0b10)
        vm.flag_overflow = bool(value & 0b100)
        vm.flag_carry = bool(value & 0b1000)
        vm.pc += 1


class LOAD(Operation):
    P = (REGISTER, U5, REGISTER)

    def execute(self, vm):
        target, offset, address = self.args

        result = vm.access_memory(vm.get_register(address) + offset)
        vm.set_zero_and_sign(result)
        vm.store_register(target, result)
        vm.pc += 1


class STORE(Operation):
    P = (REGISTER, U5, REGISTER)

    def execute(self, vm):
        source, offset, address = self.args

        vm.assign_memory(vm.get_register(address) + offset, vm.get_register(source))
        vm.pc += 1


class BR(RegisterBranch):
    @staticmethod
    def should(vm):
        return True


class BRR(RelativeBranch):
    @staticmethod
    def should(vm):
        return True


class BL(RegisterBranch):
    @staticmethod
    def should(vm):
        return vm.flag_sign ^ vm.flag_overflow


class BLR(RelativeBranch):
    @staticmethod
    def should(vm):
        return vm.flag_sign ^ vm.flag_overflow


class BGE(RegisterBranch):
    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow)


class BGER(RelativeBranch):
    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow)


class BLE(RegisterBranch):
    @staticmethod
    def should(vm):
        return (vm.flag_sign ^ vm.flag_overflow) or vm.flag_zero


class BLER(RelativeBranch):
    @staticmethod
    def should(vm):
        return (vm.flag_sign ^ vm.flag_overflow) or vm.flag_zero


class BG(RegisterBranch):
    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow) and not vm.flag_zero


class BGR(RelativeBranch):
    @staticmethod
    def should(vm):
        return not (vm.flag_sign ^ vm.flag_overflow) and not vm.flag_zero


class BULE(RegisterBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_carry or vm.flag_zero


class BULER(RelativeBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_carry or vm.flag_zero


class BUG(RegisterBranch):
    @staticmethod
    def should(vm):
        return vm.flag_carry and not vm.flag_zero


class BUGR(RelativeBranch):
    @staticmethod
    def should(vm):
        return vm.flag_carry and not vm.flag_zero


class BZ(RegisterBranch):
    @staticmethod
    def should(vm):
        return vm.flag_zero


class BZR(RelativeBranch):
    @staticmethod
    def should(vm):
        return vm.flag_zero


class BNZ(RegisterBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_zero


class BNZR(RelativeBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_zero


class BC(RegisterBranch):
    @staticmethod
    def should(vm):
        return vm.flag_carry


class BCR(RelativeBranch):
    @staticmethod
    def should(vm):
        return vm.flag_carry


class BNC(RegisterBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_carry


class BNCR(RelativeBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_carry


class BS(RegisterBranch):
    @staticmethod
    def should(vm):
        return vm.flag_sign


class BSR(RelativeBranch):
    @staticmethod
    def should(vm):
        return vm.flag_sign


class BNS(RegisterBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_sign


class BNSR(RelativeBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_sign


class BV(RegisterBranch):
    @staticmethod
    def should(vm):
        return vm.flag_overflow


class BVR(RelativeBranch):
    @staticmethod
    def should(vm):
        return vm.flag_overflow


class BNV(RegisterBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_overflow


class BNVR(RelativeBranch):
    @staticmethod
    def should(vm):
        return not vm.flag_overflow


class CALL_AND_RETURN(Operation):
    P = (REGISTER, REGISTER_OR_LABEL)

    def execute(self, vm):
        ra, rb = self.args

        old_pc = vm.pc
        vm.pc = vm.get_register(rb)
        vm.store_register(rb, old_pc + 1)
        old_fp = vm.get_register("FP")
        vm.store_register("FP", vm.get_register(ra))
        vm.store_register(ra, old_fp)

    def typecheck(self, *args, **kwargs):
        messages = super().typecheck(*args, **kwargs)
        if len(self.args) >= 1 and is_register(self.args[0]):
            with suppress(ValueError):
                i = register_to_index(self.args[0])
                if i != 12:
                    msg = "first argument to {} should be R12".format(self.name)
                    messages.warn(msg, self.args[0])
        return messages


class CALL(CALL_AND_RETURN):
    P = (REGISTER, REGISTER_OR_LABEL)

    def convert(self):
        if isinstance(self.args[1], int):
            return SET("R13", self.args[1]).convert() + [
                self.__class__(self.args[0], "R13")
            ]
        else:
            return super().convert()


class RETURN(CALL_AND_RETURN):
    P = (REGISTER, REGISTER)

    def typecheck(self, *args, **kwargs):
        messages = super().typecheck(*args, **kwargs)
        if len(self.args) >= 2 and is_register(self.args[1]):
            with suppress(ValueError):
                i = register_to_index(self.args[1])
                if i != 13:
                    messages.warn(
                        "second argument to RETURN should be R13", self.args[1]
                    )
        return messages


class SWI(Operation):
    P = (U4,)


class RTI(Operation):
    P = ()


class CMP(Operation):
    P = (REGISTER, REGISTER)

    def convert(self):
        return [FON(8), SUB("R0", self.args[0], self.args[1])]


class CON(Operation):
    P = ()

    def convert(self):
        return [FON(8)]


class COFF(Operation):
    P = ()

    def convert(self):
        return [FOFF(8)]


class CBON(Operation):
    P = ()

    def convert(self):
        return [FON(16)]


class CCBOFF(Operation):
    P = ()

    def convert(self):
        return [FOFF(24)]


class MOVE(Operation):
    P = (REGISTER, REGISTER)

    def convert(self):
        return [OR(self.args[0], self.args[1], "R0")]


class SETRF(Operation):
    P = (REGISTER, I16_OR_LABEL)

    def convert(self):
        return SET(*self.args).convert() + FLAGS(self.args[0]).convert()


class FLAGS(Operation):
    P = (REGISTER,)

    def convert(self):
        return [FOFF(8), ADD("R0", self.args[0], "R0")]


class HALT(Operation):
    P = ()

    def convert(self):
        return [BRR(0)]


class NOP(Operation):
    P = ()

    def convert(self):
        return [BRR(1)]


class NEG(Operation):
    P = (REGISTER, REGISTER)

    def convert(self):
        return [FON(8), SUB(self.args[0], "R0", self.args[1])]


class NOT(Operation):
    P = (REGISTER, REGISTER)

    def typecheck(self, *args, **kwargs):
        messages = super().typecheck(*args, **kwargs)
        if len(self.args) == 2 and is_register(self.args[1]):
            with suppress(ValueError):
                i = register_to_index(self.args[1])
                if i == 11:
                    messages.warn("don't use R11 with NOT", self.args[1])
        return messages

    def convert(self):
        return [
            SETLO("R11", 0xFF),
            SETHI("R11", 0xFF),
            XOR(self.args[0], "R11", self.args[1]),
        ]


class INTEGER(Operation):
    P = (I16,)

    def execute(self, vm):
        vm.assign_memory(vm.dc, to_u16(self.args[0]))
        vm.dc += 1


class DSKIP(Operation):
    P = (U16,)

    def execute(self, vm):
        vm.dc += self.args[0]


class LP_STRING(Operation):
    P = (STRING,)

    def execute(self, vm):
        vm.assign_memory(vm.dc, len(self.args[0]))
        vm.dc += 1
        for c in self.args[0]:
            vm.assign_memory(vm.dc, ord(c))
            vm.dc += 1


class CONSTANT(Operation):
    P = (LABEL_TYPE, I16)

    def convert(self):
        return []


class LABEL(Operation):
    P = (LABEL_TYPE,)

    def convert(self):
        return []


class DLABEL(Operation):
    P = (LABEL_TYPE,)

    def convert(self):
        return []


class PRINT_REG(Operation):
    P = (REGISTER,)

    def execute(self, vm):
        v = vm.get_register(self.args[0])
        print("{} = {}".format(self.args[0], format_int(v)))
        vm.pc += 1


class PRINT(Operation):
    P = (STRING,)

    def execute(self, vm):
        print(self.args[0], end="")
        vm.pc += 1


class PRINTLN(Operation):
    P = (STRING,)

    def execute(self, vm):
        print(self.args[0])
        vm.pc += 1


class __EVAL(Operation):
    P = (STRING,)

    def execute(self, vm):
        # Rudimentary safeguard to make execution of malicious code harder. Users of
        # hera-py should keep in mind that running arbitrary HERA code is no safer than
        # running arbitrary code of any kind.
        if "import" not in self.args[0]:
            bytecode = compile(self.args[0], "<string>", "exec")
            exec(bytecode, {}, {"vm": vm})

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
    if not isinstance(arg, Token) or arg.type != "REGISTER":
        return "expected register"

    if arg.lower() == "pc":
        return "program counter cannot be accessed or changed directly"

    try:
        register_to_index(arg)
    except ValueError:
        return "{} is not a valid register".format(arg)
    else:
        return None


def check_register_or_label(arg, symbol_table: Dict[str, int]) -> Optional[str]:
    if not isinstance(arg, Token) or arg.type not in ("REGISTER", "SYMBOL"):
        return "expected register or label"

    if arg.type == "REGISTER":
        return check_register(arg)
    else:
        try:
            val = symbol_table[arg]
        except KeyError:
            return "undefined symbol"
        else:
            if isinstance(val, Constant):
                return "constant cannot be used as label"
            elif isinstance(val, DataLabel):
                return "data label cannot be used as branch label"
            else:
                return None


def check_label(arg) -> Optional[str]:
    if not is_symbol(arg):
        return "expected label"
    else:
        return None


def check_string(arg):
    if not isinstance(arg, Token) or arg.type != "STRING":
        return "expected string literal"
    else:
        return None


def check_in_range(arg, symbol_table, *, lo, hi, labels=False):
    if is_symbol(arg):
        try:
            arg = symbol_table[arg]
        except KeyError:
            return "undefined constant"
        else:
            if not labels and not isinstance(arg, Constant):
                return "cannot use label as constant"

    if not isinstance(arg, int):
        return "expected integer"

    if arg < lo or arg >= hi:
        return "integer must be in range [{}, {})".format(lo, hi)
    else:
        return None


def resolve_ops(program: List[Op]) -> Tuple[List[Operation], Messages]:
    """Replace all Op objects with their corresponding class from hera/op.py. Operations
    with unrecognized names are not included in the return value.
    """
    messages = Messages()
    ret = []
    for op in program:
        try:
            cls = name_to_class[op.name]
        except KeyError:
            messages.err("unknown instruction `{}`".format(op.name), loc=op.name)
        else:
            ret.append(cls(*op.args, loc=op.name))
    return (ret, messages)


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
