import sys


REGISTER = "r"


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
            self.emit_error(
                "too few args to {} (expected {}, got {})".format(name, nexpected, ngot)
            )
            ret = False

        if nexpected < ngot:
            self.emit_error(
                "too many args to {} (expected {}, got {})".format(name, nexpected, ngot)
            )
            ret = False

        ordinals = ["first", "second", "third"]
        for ordinal, pattern, arg in zip(ordinals, self.params, self.args):
            prefix = "{} arg to {} ".format(ordinal, name)
            error = self.assert_one_arg(pattern, arg)
            if error:
                self.emit_error(prefix + error, column=arg.column)
                ret = False

        return ret

    def _verify_one_arg(self, pattern, arg):
        """Verify that the argument matches the pattern. Return a string stating the
        error if it doesn't, return None otherwise.
        """
        if pattern == self.REGISTER:
            if not isinstance(arg, Token) or arg.type != "REGISTER":
                return "not a register"

            try:
                register_to_index(arg)
            except ValueError:
                return "not a valid register"
        elif pattern == self.REGISTER_OR_LABEL:
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

    def convert_pseudo(self):
        return [self]

    def exec(self, vm):
        raise NotImplementedError

    def emit_error(self, msg, *, column=None):
        pass

    def __eq__(self, other):
        return self.args == other.args


class Add(Instruction):
    name = "ADD"
    params = (REGISTER, REGISTER)
