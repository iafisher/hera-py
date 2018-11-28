import sys
from collections import namedtuple

from lark import Token

from .utils import from_u16, register_to_index, to_u16


REGISTER = "r"
REGISTER_OR_LABEL = "rl"
I8 = range(-2 ** 7, 2 ** 8)
I16 = range(-2 ** 15, 2 ** 16)


"""
1. Verify instructions.
2. Expand pseudo-instructions.
3. Resolve labels and constants.
"""


VerifyErrorInfo = namedtuple("VerifyErrorInfo", ["msg", "line", "col"])
VerifyErrorInfo.__new__.__defaults__ = (None,)


class Instruction:
    def __init__(self, *args, lineno=None, line=None):
        self.args = list(args)
        self.lineno = lineno
        self.line = line

    def verify(self):
        errors = []

        ngot = len(self.args)
        nexpected = len(self.params)

        if ngot < nexpected:
            errors.append(
                VerifyErrorInfo(
                    "too few args to {} (expected {}, got {})".format(
                        self.name, nexpected, ngot
                    ),
                    self.lineno,
                )
            )

        if nexpected < ngot:
            errors.append(
                VerifyErrorInfo(
                    "too many args to {} (expected {}, got {})".format(
                        self.name, nexpected, ngot
                    ),
                    self.lineno,
                )
            )

        ordinals = ["first", "second", "third"]
        for ordinal, pattern, arg in zip(ordinals, self.params, self.args):
            prefix = "{} arg to {} ".format(ordinal, self.name)
            error = self._verify_one_arg(pattern, arg)
            if error:
                errors.append(VerifyErrorInfo(prefix + error, self.lineno, arg.column))

        return errors

    def _verify_one_arg(self, pattern, arg):
        """Verify that the argument matches the pattern. Return a string stating the
        error if it doesn't, return None otherwise.
        """
        if pattern == REGISTER:
            if not isinstance(arg, Token) or arg.type != "REGISTER":
                return "not a register"

            try:
                register_to_index(arg)
            except ValueError:
                return "not a valid register"
        elif pattern == REGISTER_OR_LABEL:
            if not isinstance(arg, Token):
                return "not a register or label"

            if arg.type == "REGISTER":
                try:
                    register_to_index(arg)
                except ValueError:
                    return "not a valid register"
            elif arg.type != "SYMBOL":
                return "not a register or label"
        elif isinstance(pattern, range):
            if isinstance(arg, Token) and arg.type == "SYMBOL":
                # Symbols will be resolved later.
                return None

            if not isinstance(arg, int):
                return "not an integer"
            if arg not in pattern:
                if pattern.start == 0 and arg < 0:
                    return "must not be negative"
                else:
                    return "out of range"
        else:
            raise RuntimeError(
                "unknown pattern in Instruction._verify_one_arg", pattern
            )

    def convert(self):
        return [self]

    def execute(self, vm):
        raise NotImplementedError

    def __eq__(self, other):
        return self.args == other.args

    def __repr__(self):
        return "{0.__class__.__name__}({1})".format(
            self, ", ".join(map(repr, self.args))
        )


class Set(Instruction):
    name = "SET"
    params = (REGISTER, I16)

    def convert(self):
        d, v = self.args
        if isinstance(v, int):
            v = to_u16(v)
            lo = v & 0xFF
            hi = v >> 8

            if hi:
                return [Setlo(d, lo), Sethi(d, hi)]
            else:
                return [Setlo(d, lo)]
        else:
            return [Setlo(d, v), Sethi(d, v)]


class Setlo(Instruction):
    name = "SETLO"
    params = (REGISTER, I8)

    def execute(self, vm):
        target, value = self.args
        if value > 127:
            value -= 256
        vm.store_register(target, to_u16(value))
        vm.pc += 1


class Sethi(Instruction):
    name = "SETHI"
    params = (REGISTER, I8)

    def execute(self, vm):
        target, value = self.args
        vm.store_register(target, (value << 8) + (vm.get_register(target) & 0x00FF))
        vm.pc += 1


class Inc(Instruction):
    name = "INC"
    params = (REGISTER, range(1, 65))

    def execute(self, vm):
        target, value = self.args
        original = vm.get_register(target)
        result = (value + original) & 0xFFFF
        vm.store_register(target, result)

        vm.set_zero_and_sign(result)
        vm.flag_overflow = from_u16(result) != from_u16(original) + value
        vm.flag_carry = value + original >= 2 ** 16
        vm.pc += 1


class Dec(Instruction):
    name = "DEC"
    params = (REGISTER, range(1, 65))

    def execute(self, vm):
        target, value = self.args
        original = vm.get_register(target)
        result = to_u16((original - value) & 0xFFFF)
        vm.store_register(target, result)

        vm.set_zero_and_sign(result)
        vm.flag_overflow = from_u16(result) != from_u16(original) - value
        vm.flag_carry = original < value
        vm.pc += 1


class Add(Instruction):
    name = "ADD"
    params = (REGISTER, REGISTER)


def emit_error(msg, *, column=None):
    # TODO: Should probably move this to utils
    sys.stderr.write(msg + "\n")
