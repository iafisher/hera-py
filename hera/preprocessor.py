"""Preprocess HERA programs to convert pseudo-instructions and resolve labels.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
from lark import Token

from .parser import Op
from .utils import register_to_index, to_u16, HERAError


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
                    # Fill in line number if not already present.
                    if not e.line:
                        e.line = op.name.line
                    raise e

        program = self.convert_pseudo_instructions(program)
        program = self.preprocess_second_pass(program)
        return program

    def convert_pseudo_instructions(self, program):
        """Convert the pseudo-instructions in the program. It guarantees that labels
        will only appear as the second argument of SETLO and SETHI.
        """
        nprogram = []
        for op in program:
            try:
                handler = getattr(self, "convert_" + op.name.lower())
            except AttributeError:
                if op.name.upper().startswith("B") and is_symbol(op.args[0]):
                    l = op.args[0]
                    # Note that we MUST use SETLO+SETHI and not SET, because the next
                    # pass only handles label resolution and does not further expand
                    # pseudo-instructions.
                    setlo = copy_token("SETLO", op.name)
                    sethi = copy_token("SETHI", op.name)
                    nprogram.append(Op(setlo, ["R11", l]))
                    nprogram.append(Op(sethi, ["R11", l]))
                    nprogram.append(Op(op.name, ["R11"]))
                else:
                    nprogram.append(op)
            else:
                new_ops = handler(*op.args)
                # Copy over the line number and column information from the old op.
                new_ops = [
                    Op(copy_token(new_op.name, op.name), new_op.args)
                    for new_op in new_ops
                ]
                nprogram.extend(new_ops)
        return nprogram

    def preprocess_second_pass(self, program):
        """Run the second pass of the preprocessor. This pass resolves labels
        into their actual line numbers. It assumes that labels only appear as
        the second argument of SETLO and SETHI (the convert_pseudo_instructions
        method guarantees this).
        """
        self.get_labels(program)

        nprogram = []
        for op in program:
            if op.name.upper() == "SETLO" and is_symbol(op.args[1]):
                d, v = op.args
                name = copy_token("SETLO", op.name)
                nprogram.append(Op(name, [d, self.labels[v] & 0xFF]))
            elif op.name.upper() == "SETHI" and is_symbol(op.args[1]):
                d, v = op.args
                name = copy_token("SETHI", op.name)
                nprogram.append(Op(name, [d, self.labels[v] >> 8]))
            elif op.name.upper() in ("LABEL", "DLABEL", "CONSTANT"):
                continue
            else:
                nprogram.append(op)
        return nprogram

    def get_labels(self, program):
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
    REGISTER_OR_LABEL = "rl"
    STRING = "s"
    U4 = range(0, 2 ** 4)
    U5 = range(0, 2 ** 5)
    U16 = range(0, 2 ** 16)
    I8 = range(-128, 256)

    def assert_args(self, name, expected, got):
        """Assert that the given args match the expected ones and raise a
        HERAError otherwise. `name` is the name of the HERA op. `expected` is
        a tuple or list of constants (REGISTER, U16, etc., defined above)
        representing the expected argument types to the operation. `args` is
        a tuple or list of the actual arguments given.
        """
        if len(got) < len(expected):
            raise HERAError(
                "too few args to {} (expected {})".format(name, len(expected))
            )

        if len(expected) < len(got):
            raise HERAError(
                "too many args to {} (expected {})".format(name, len(expected))
            )

        ordinals = ["first", "second", "third"]
        for ordinal, pattern, arg in zip(ordinals, expected, got):
            prefix = "{} arg to {} ".format(ordinal, name)
            error = self.assert_one_arg(pattern, arg)
            if error:
                raise HERAError(prefix + error, line=arg.line, column=arg.column)

    def assert_one_arg(self, pattern, arg):
        """Assert that the argument matches the pattern. Return a string stating the
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
            if is_symbol(arg):
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
                "unknown pattern in Preprocessor.assert_one_arg", pattern
            )

    def verify_set(self, *args):
        self.assert_args("SET", [self.REGISTER, range(-32768, 65536)], args)

    def verify_setlo(self, *args):
        self.assert_args("SETLO", [self.REGISTER, range(-128, 256)], args)

    def verify_sethi(self, *args):
        self.assert_args("SETHI", [self.REGISTER, range(0, 256)], args)

    def verify_and(self, *args):
        self.assert_args("AND", [self.REGISTER] * 3, args)

    def verify_or(self, *args):
        self.assert_args("OR", [self.REGISTER] * 3, args)

    def verify_add(self, *args):
        self.assert_args("ADD", [self.REGISTER] * 3, args)

    def verify_sub(self, *args):
        self.assert_args("SUB", [self.REGISTER] * 3, args)

    def verify_mul(self, *args):
        self.assert_args("MUL", [self.REGISTER] * 3, args)

    def verify_xor(self, *args):
        self.assert_args("XOR", [self.REGISTER] * 3, args)

    def verify_inc(self, *args):
        self.assert_args("INC", [self.REGISTER, range(1, 65)], args)

    def verify_dec(self, *args):
        self.assert_args("DEC", [self.REGISTER, range(1, 65)], args)

    def verify_lsl(self, *args):
        self.assert_args("LSL", [self.REGISTER] * 2, args)

    def verify_lsr(self, *args):
        self.assert_args("LSR", [self.REGISTER] * 2, args)

    def verify_lsl8(self, *args):
        self.assert_args("LSL8", [self.REGISTER] * 2, args)

    def verify_lsr8(self, *args):
        self.assert_args("LSR8", [self.REGISTER] * 2, args)

    def verify_asl(self, *args):
        self.assert_args("ASL", [self.REGISTER] * 2, args)

    def verify_asr(self, *args):
        self.assert_args("ASR", [self.REGISTER] * 2, args)

    def verify_savef(self, *args):
        self.assert_args("SAVEF", [self.REGISTER], args)

    def verify_rstrf(self, *args):
        self.assert_args("RSTRF", [self.REGISTER], args)

    def verify_fon(self, *args):
        self.assert_args("FON", [self.U4], args)

    def verify_foff(self, *args):
        self.assert_args("FOFF", [self.U4], args)

    def verify_fset5(self, *args):
        self.assert_args("FSET5", [self.U4], args)

    def verify_fset4(self, *args):
        self.assert_args("FSET4", [self.U4], args)

    def verify_load(self, *args):
        self.assert_args("LOAD", [self.REGISTER, self.U5, self.REGISTER], args)

    def verify_store(self, *args):
        self.assert_args("STORE", [self.REGISTER, self.U5, self.REGISTER], args)

    def verify_br(self, *args):
        self.assert_args("BR", [self.REGISTER_OR_LABEL], args)

    def verify_brr(self, *args):
        self.assert_args("BRR", [self.I8], args)

    def verify_bl(self, *args):
        self.assert_args("BL", [self.REGISTER_OR_LABEL], args)

    def verify_blr(self, *args):
        self.assert_args("BLR", [self.I8], args)

    def verify_bge(self, *args):
        self.assert_args("BGE", [self.REGISTER_OR_LABEL], args)

    def verify_bger(self, *args):
        self.assert_args("BGER", [self.I8], args)

    def verify_ble(self, *args):
        self.assert_args("BLE", [self.REGISTER_OR_LABEL], args)

    def verify_bler(self, *args):
        self.assert_args("BLER", [self.I8], args)

    def verify_bg(self, *args):
        self.assert_args("BG", [self.REGISTER_OR_LABEL], args)

    def verify_bgr(self, *args):
        self.assert_args("BGR", [self.I8], args)

    def verify_bule(self, *args):
        self.assert_args("BULE", [self.REGISTER_OR_LABEL], args)

    def verify_buler(self, *args):
        self.assert_args("BULER", [self.I8], args)

    def verify_bug(self, *args):
        self.assert_args("BUG", [self.REGISTER_OR_LABEL], args)

    def verify_bugr(self, *args):
        self.assert_args("BUGR", [self.I8], args)

    def verify_bz(self, *args):
        self.assert_args("BZ", [self.REGISTER_OR_LABEL], args)

    def verify_bzr(self, *args):
        self.assert_args("BZR", [self.I8], args)

    def verify_bnz(self, *args):
        self.assert_args("BNZ", [self.REGISTER_OR_LABEL], args)

    def verify_bnzr(self, *args):
        self.assert_args("BNZR", [self.I8], args)

    def verify_bc(self, *args):
        self.assert_args("BC", [self.REGISTER_OR_LABEL], args)

    def verify_bcr(self, *args):
        self.assert_args("BCR", [self.I8], args)

    def verify_bnc(self, *args):
        self.assert_args("BNC", [self.REGISTER_OR_LABEL], args)

    def verify_bncr(self, *args):
        self.assert_args("BNCR", [self.I8], args)

    def verify_bs(self, *args):
        self.assert_args("BS", [self.REGISTER_OR_LABEL], args)

    def verify_bsr(self, *args):
        self.assert_args("BSR", [self.I8], args)

    def verify_bns(self, *args):
        self.assert_args("BNS", [self.REGISTER_OR_LABEL], args)

    def verify_bnsr(self, *args):
        self.assert_args("BNSR", [self.I8], args)

    def verify_bv(self, *args):
        self.assert_args("BV", [self.REGISTER_OR_LABEL], args)

    def verify_bvr(self, *args):
        self.assert_args("BVR", [self.I8], args)

    def verify_bnv(self, *args):
        self.assert_args("BNV", [self.REGISTER_OR_LABEL], args)

    def verify_bnvr(self, *args):
        self.assert_args("BNVR", [self.I8], args)

    def verify_call(self, *args):
        self.assert_args("CALL", [self.REGISTER, self.REGISTER_OR_LABEL], args)

    def verify_return(self, *args):
        self.assert_args("RETURN", [self.REGISTER, self.REGISTER_OR_LABEL], args)

    def convert_set(self, d, v):
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

    def convert_cmp(self, a, b):
        return [Op("FON", [8]), Op("SUB", ["R0", a, b])]

    def convert_con(self):
        return [Op("FON", [8])]

    def convert_coff(self):
        return [Op("FOFF", [8])]

    def convert_cbon(self):
        return [Op("FON", [16])]

    def convert_ccboff(self):
        return [Op("FOFF", [24])]

    def convert_move(self, a, b):
        return [Op("OR", [a, b, "R0"])]

    def convert_setrf(self, d, v):
        return self.convert_set(d, v) + self.convert_flags(d)

    def convert_flags(self, a):
        return [Op("FOFF", [8]), Op("ADD", ["R0", a, "R0"])]

    def convert_halt(self):
        return [Op("BRR", [0])]

    def convert_nop(self):
        return [Op("BRR", [1])]

    def convert_call(self, a, l):
        if is_symbol(l):
            return [
                Op("SETLO", ["R13", l]),
                Op("SETHI", ["R13", l]),
                Op("CALL", [a, "R13"]),
            ]
        else:
            return [Op("CALL", [a, l])]

    def convert_neg(self, d, b):
        return [Op("FON", [8]), Op("SUB", [d, "R0", b])]

    def convert_not(self, d, b):
        return [
            Op("SETLO", ["R11", 0xFF]),
            Op("SETHI", ["R11", 0xFF]),
            Op("XOR", [d, "R11", b]),
        ]


def copy_token(val, otkn):
    return Token(otkn.type, val, line=otkn.line, column=otkn.column)


def is_symbol(s):
    return isinstance(s, Token) and s.type == "SYMBOL"
