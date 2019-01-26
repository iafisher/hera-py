from hera.data import Op
from hera.utils import from_u16, print_register_debug, to_u16


class Operation:
    # TODO: Name of this class is confusingly similar to hera.data.Op

    def __init__(self, *args, loc=None):
        self.args = args
        self.loc = loc

    def typecheck(self):
        return check_arglist(self.P, self.args)

    def convert(self):
        return [self]

    def assemble(self):
        raise NotImplementedError

    def execute(self, vm):
        raise NotImplementedError


REGISTER = "register"
REGISTER_OR_LABEL = "register or label"
STRING = "string literal"
I16 = "signed 16-bit integer"
U16 = "unsigned 16-bit integer"
I8 = "signed 8-bit integer"
I8_OR_LABEL = "signed 8-bit integer or label"
U5 = "unsigned 5-bit integer"
U4 = "unsigned 4-bit integer"


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
            lbl = self.args[0]
            return [
                SETLO("R11", lbl & 0xFF),
                SETHI("R11", lbl >> 8),
                self.__class__("R11"),
            ]
        else:
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
    P = (REGISTER, I16)

    def convert(self):
        dest, value = self.args
        if isinstance(value, int):
            value = to_u16(value)
            lo = value & 0xFF
            hi = value >> 8
            return [SETLO(dest, lo, loc=self.loc), SETHI(dest, hi, loc=self.loc)]
        else:
            # TODO: When does this case actually happen?
            return [SETLO(dest, value), SETHI(dest, value)]


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

        original = self.get_register(target)
        result = to_u16((original - value) & 0xFFFF)
        self.store_register(target, result)

        self.set_zero_and_sign(result)
        self.flag_overflow = from_u16(result) != from_u16(original) - value
        self.flag_carry = original < value
        self.pc += 1


class LSL(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        carry = 1 if vm.flag_carry and not vm.flag_carry_block else 0
        result = ((arg << 1) + carry) & 0xFFFF

        vm.flag_carry = original & 0x8000

        return result


class LSR(UnaryOp):
    @staticmethod
    def calculate(vm, arg):
        carry = 2 ** 15 if vm.flag_carry and not vm.flag_carry_block else 0
        result = (arg >> 1) + carry

        vm.flag_carry = original % 2 == 1

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

        vm.flag_carry = original & 0x8000
        vm.flag_overflow = original & 0x8000 and not result & 0x8000

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


class CALL(Operation):
    P = (REGISTER, REGISTER_OR_LABEL)

    def execute(self, vm):
        ra, rb = self.args

        old_pc = vm.pc
        vm.pc = vm.get_register(rb)
        vm.store_register(rb, old_pc + 1)
        old_fp = vm.get_register("FP")
        vm.store_register("FP", vm.get_register(ra))
        vm.store_register(ra, old_fp)

    def convert(self):
        if isinstance(self.args[1], int):
            return SET("R13", self.args[1]).convert() + CALL(self.args[0], "R13")
        else:
            return super().convert()


class RETURN(Operation):
    P = (REGISTER, REGISTER_OR_LABEL)

    def execute(self, vm):
        ra, rb = self.args

        old_pc = vm.pc
        vm.pc = vm.get_register(rb)
        vm.store_register(rb, old_pc + 1)
        old_fp = vm.get_register("FP")
        vm.store_register("FP", vm.get_register(ra))
        vm.store_register(ra, old_fp)


class SWI(Operation):
    P = (U4,)

    def execute(self, vm):
        if not vm.warned_for_SWI:
            vm.print_warning("SWI is a no-op in this simulator", loc=vm.location)
            vm.warned_for_SWI = True
        vm.pc += 1


class RTI(Operation):
    P = ()

    def execute(self, vm):
        if not vm.warned_for_RTI:
            vm.print_warning("RTI is a no-op in this simulator", loc=vm.location)
            vm.warned_for_RTI = True
        vm.pc += 1


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
    P = (REGISTER, I16)

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
        # TODO: This doesn't seem right.
        vm.pc += 1


class DSKIP(Operation):
    P = (U16,)

    def execute(self, vm):
        vm.dc += self.args[0]
        vm.pc += 1


class LP_STRING(Operation):
    P = (STRING,)

    def execute(self, vm):
        vm.assign_memory(vm.dc, len(self.args[0]))
        vm.dc += 1
        for c in self.args[0]:
            vm.assign_memory(vm.dc, ord(c))
            vm.dc += 1
        vm.pc += 1


class PRINT_REG(Operation):
    P = (REGISTER,)

    def execute(self, vm):
        v = vm.get_register(self.args[0])
        print_register_debug(self.args[0], v, to_stderr=False)
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

        self.pc += 1


def check_arglist(argtypes, args):
    errors = []
    if len(argtypes) != len(args):
        errors.append("wrong number of arguments")

    errors = []
    for expected, got in zip(argtypes, args):
        if expected == REGISTER:
            errors += check_register(got)
        elif expected == I16:
            errors += check_i16(got)
        elif isinstance(expected, range):
            errors += check_range(expected, got)
        else:
            raise RuntimeError(
                "unknown parameter type {}".format(expected.__class__.__name__)
            )
    return errors


name_to_class = {"ADD": Add, "MUL": Mul, "SUB": Sub}
