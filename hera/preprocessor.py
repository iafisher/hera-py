"""Preprocess HERA programs to convert pseudo-instructions and resolve labels.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
from lark import Token

from .parser import Op
from .utils import to_u16, HERAError


# Arbitrary value copied over from HERA-C.
HERA_DATA_START = 16743


def preprocess(program):
    """Preprocess the program (a list of Op objects) into valid input for the
    exec_many method on the VirtualMachine class.

    This function does the following
        - Replaces pseudo-instructions with real ones
        - Verifies the correct usage of instructions
        - Resolves labels into their line numbers.
    """
    helper = Preprocessor()
    return helper.preprocess(program)


def branch_preprocessor(name):
    """A factory method to create handlers for branch instructions. All of
    these receive the same first-pass translation, which replaces the use of a
    label with a SET(R11, label) BRANCH(R11) combination.
    """

    def preprocess1_XXX(self, l):
        if isinstance(l, Token) and l.type == "SYMBOL":
            # Note that we MUST use SETLO+SETHI and not SET, because the next
            # pass only handles label resolution and does not further expand
            # pseudo-instructions.
            return [Op("SETLO", ["R11", l]), Op("SETHI", ["R11", l]), Op(name, ["R11"])]
        else:
            return [Op(name, [l])]

    return preprocess1_XXX


class Preprocessor:
    """A helper class for preprocessing programs. Do not instantiate this class
    directly. Use the module-level assemble function instead.
    """

    def __init__(self):
        self.labels = {}

    def preprocess(self, program):
        """See docstring for module-level preprocess for details."""
        for op in program:
            try:
                verifier = getattr(self, "verify_" + op.name.lower())
            except AttributeError:
                pass
            else:
                try:
                    verifier(*op.args)
                except HERAError as e:
                    e.line = op.name.line
                    raise e

        program = self.preprocess_first_pass(program)
        program = self.preprocess_second_pass(program)
        return program

    def preprocess_first_pass(self, program):
        """Run the first pass of the preprocessor. This pass converts pseudo-
        instructions to real ones, but does not resolve labels. It does however
        guarantee that labels will only appear as the second argument of SETLO
        and SETHI.
        """
        nprogram = []
        for op in program:
            try:
                handler = getattr(self, "preprocess1_" + op.name.lower())
            except AttributeError:
                nprogram.append(op)
            else:
                nprogram.extend(handler(*op.args))
        return nprogram

    def preprocess_second_pass(self, program):
        """Run the second pass of the preprocessor. This pass resolves labels
        into their actual line numbers. It assumes that labels only appear as
        the second argument of SETLO and SETHI (the preprocess_first_pass
        method guarantees this).
        """
        self.resolve_labels(program)

        nprogram = []
        for op in program:
            try:
                handler = getattr(self, "preprocess2_" + op.name.lower())
            except AttributeError:
                nprogram.append(op)
            else:
                nop = handler(*op.args)
                if nop:
                    nprogram.append(nop)
        return nprogram

    def resolve_labels(self, program):
        """Populate the `labels` field with the instruction and data labels of
        the program.
        """
        pc = 0
        dc = HERA_DATA_START
        for op in program:
            opname = op.name.lower()
            if opname == "label":
                self.labels[op.args[0]] = pc
            elif opname == "dlabel":
                self.labels[op.args[0]] = dc
            elif opname == "constant":
                self.labels[op.args[0]] = op.args[1]
            elif opname == "integer":
                dc += 1
            elif opname == "dskip":
                dc += op.args[0]
            elif opname == "lp_string":
                dc += len(op.args[0]) + 1
            else:
                pc += 1

    # Constants to pass to verify_base
    REGISTER = "r"
    STRING = "s"
    U16 = "u16"
    I8 = "i8"

    def assert_args(self, name, expected, got):
        """Assert that the given args match the expected ones and raise a
        HERAError otherwise. `name` is the name of the HERA op. `expected` is
        a tuple or list of constants (REGISTER, U16, etc., defined above)
        representing the expected argument types to the operation. `args` is
        a tuple or list of the actual arguments given.
        """
        if len(got) < len(expected):
            raise HERAError("too few args to " + name)

        if len(expected) < len(got):
            raise HERAError("too many args to " + name)

        ordinals = ["first", "second", "third"]
        for ordinal, pattern, arg in zip(ordinals, expected, got):
            prefix = "{} arg to {} ".format(ordinal, name)
            if pattern == self.REGISTER:
                if not isinstance(arg, Token) or arg.type != "REGISTER":
                    raise HERAError(prefix + "not a register")
            elif pattern == self.U16:
                if not isinstance(arg, int):
                    raise HERAError(prefix + "not an integer")
                if arg < 0:
                    raise HERAError(prefix + "must not be negative")
                if arg > 65535:
                    raise HERAError(prefix + "out of range")
            elif pattern == self.I8:
                if not isinstance(arg, int):
                    raise HERAError(prefix + "not an integer")
                if not (-128 <= arg <= 127):
                    raise HERAError(prefix + "out of range")
            else:
                raise RuntimeError("unknown pattern " + pattern)

    def verify_setlo(self, *args):
        self.assert_args("SETLO", (self.REGISTER, self.I8), args)

    def preprocess1_set(self, d, v):
        if isinstance(v, int):
            v = to_u16(v)
            lo = v & 0xFF
            hi = v >> 8
            if hi:
                return [Op("SETLO", [d, lo]), Op("SETHI", [d, hi])]
            else:
                return [Op("SETLO", [d, lo])]
        else:
            return [Op("SETLO", [d, v]), Op("SETHI", [d, v])]

    def preprocess1_cmp(self, a, b):
        return [Op("FON", [8]), Op("SUB", ["R0", a, b])]

    def preprocess1_con(self):
        return [Op("FON", [8])]

    def preprocess1_coff(self):
        return [Op("FOFF", [8])]

    def preprocess1_cbon(self):
        return [Op("FON", [16])]

    def preprocess1_ccboff(self):
        return [Op("FOFF", [24])]

    def preprocess1_move(self, a, b):
        return [Op("OR", [a, b, "R0"])]

    def preprocess1_setrf(self, d, v):
        return self.preprocess1_set(d, v) + self.preprocess1_flags(d)

    def preprocess1_flags(self, a):
        return [Op("FOFF", [8]), Op("ADD", ["R0", a, "R0"])]

    def preprocess1_halt(self):
        return [Op("BRR", [0])]

    def preprocess1_nop(self):
        return [Op("BRR", [1])]

    def preprocess1_call(self, a, l):
        if isinstance(l, Token) and l.type == "SYMBOL":
            return [
                Op("SETLO", ["R13", l]),
                Op("SETHI", ["R13", l]),
                Op("CALL", [a, "R13"]),
            ]
        else:
            return [Op("CALL", [a, l])]

    def preprocess1_neg(self, d, b):
        return [Op("FON", [8]), Op("SUB", [d, "R0", b])]

    def preprocess1_not(self, d, b):
        return [
            Op("SETLO", ["R11", 0xFF]),
            Op("SETHI", ["R11", 0xFF]),
            Op("XOR", [d, "R11", b]),
        ]

    # Assembling branch instructions. Read the docstring of branch_preprocessor
    # for details.
    preprocess1_br = branch_preprocessor("BR")
    preprocess1_bl = branch_preprocessor("BL")
    preprocess1_bge = branch_preprocessor("BGE")
    preprocess1_ble = branch_preprocessor("BLE")
    preprocess1_bg = branch_preprocessor("BG")
    preprocess1_bule = branch_preprocessor("BULE")
    preprocess1_bug = branch_preprocessor("BUG")
    preprocess1_bz = branch_preprocessor("BZ")
    preprocess1_bnz = branch_preprocessor("BNZ")
    preprocess1_bc = branch_preprocessor("BC")
    preprocess1_bnc = branch_preprocessor("BNC")
    preprocess1_bs = branch_preprocessor("BS")
    preprocess1_bns = branch_preprocessor("BNS")
    preprocess1_bv = branch_preprocessor("BV")
    preprocess1_bnv = branch_preprocessor("BNV")

    def preprocess2_label(self, l):
        # Labels do not result in any machine code instructions.
        return None

    def preprocess2_dlabel(self, l):
        return None

    def preprocess2_constant(self, s, v):
        return None

    def preprocess2_setlo(self, d, v):
        # Label as second argument of SETLO must be replaced with line number.
        if isinstance(v, Token) and v.type == "SYMBOL":
            return Op("SETLO", [d, self.labels[v] & 0xFF])
        else:
            return Op("SETLO", [d, v])

    def preprocess2_sethi(self, d, v):
        # Label as second argument of SETHI must be replaced with line number.
        if isinstance(v, Token) and v.type == "SYMBOL":
            return Op("SETHI", [d, self.labels[v] >> 8])
        else:
            return Op("SETHI", [d, v])
