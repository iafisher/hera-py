import sys

from lark import Token

from .utils import register_to_index, to_u16


REGISTER = "r"
REGISTER_OR_LABEL = "rl"
I16 = range(-2**15, 2**16)


"""
1. Verify instructions.
2. Expand pseudo-instructions.
3. Resolve labels and constants.
"""


class Instruction:
    def __init__(self, *args, lineno=None, line=None):
        self.args = list(args)
        self.lineno = lineno
        self.line = line

    def verify(self):
        # Return this value at the end instead of immediately after an error is
        # detected so that as many errors as possible are caught, not just the first.
        ret = True

        ngot = len(self.args)
        nexpected = len(self.params)

        if ngot < nexpected:
            emit_error(
                "too few args to {} (expected {}, got {})".format(self.name, nexpected, ngot)
            )
            ret = False

        if nexpected < ngot:
            emit_error(
                "too many args to {} (expected {}, got {})".format(self.name, nexpected, ngot)
            )
            ret = False

        ordinals = ["first", "second", "third"]
        for ordinal, pattern, arg in zip(ordinals, self.params, self.args):
            prefix = "{} arg to {} ".format(ordinal, self.name)
            error = self._verify_one_arg(pattern, arg)
            if error:
                emit_error(prefix + error, column=arg.column)
                ret = False

        return ret

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
        return '{0.__class__.__name__}({1})'.format(self, ', '.join(map(repr, self.args)))


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
    def execute(self, vm):
        target, value = self.args
        if value > 127:
            value -= 256
        vm.store_register(target, to_u16(value))
        vm.pc += 1


class Sethi(Instruction):
    pass


class Add(Instruction):
    name = "ADD"
    params = (REGISTER, REGISTER)


def emit_error(msg, *, column=None):
    # TODO: Should probably move this to utils
    sys.stderr.write(msg + "\n")
