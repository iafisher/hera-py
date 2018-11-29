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
        - Replaces pseudo-instructions with real ones.
        - Verifies the correct usage of instructions.
        - Resolves labels into their line numbers.
    """
    for op in program:
        params = _params_map.get(op.name.upper())
        if params is None and op.name.upper().startswith("B"):
            if op.name.upper().endswith("R") and len(op.name) > 2:
                params = (I8,)
            else:
                params = (REGISTER_OR_LABEL,)
        if params is not None:
            try:
                verify_args(op.name, params, op.args)
            except HERAError as e:
                # Fill in line number if not already present.
                if not e.line:
                    e.line = op.name.line
                raise e

    program = convert_pseudo_instructions(program)
    program = preprocess_second_pass(program)
    return program


def convert_pseudo_instructions(program):
    """Convert the pseudo-instructions in the program. It guarantees that labels will
    only appear as the second argument of SETLO and SETHI.
    """
    nprogram = []
    for op in program:
        if op.name.upper().startswith("B") and is_symbol(op.args[0]):
            l = op.args[0]
            # Note that we MUST use SETLO+SETHI and not SET, because the next
            # pass only handles label resolution and does not further expand
            # pseudo-instructions.
            new_ops = [Op("SETLO", ["R11", l]), Op("SETHI", ["R11", l]), Op(op.name, ["R11"])]
        else:
            new_ops = convert(op)
        # Copy over the line number and column information from the old op.
        new_ops = [
            Op(copy_token(new_op.name, op.name), new_op.args)
            for new_op in new_ops
        ]
        nprogram.extend(new_ops)
    return nprogram


def preprocess_second_pass(program):
    """Run the second pass of the preprocessor. This pass resolves labels into their
    actual line numbers. It assumes that labels only appear as the second argument of 
    SETLO and SETHI (the convert_pseudo_instructions method guarantees this).
    """
    labels = get_labels(program)

    nprogram = []
    for op in program:
        if op.name.upper() == "SETLO" and is_symbol(op.args[1]):
            d, v = op.args
            name = copy_token("SETLO", op.name)
            nprogram.append(Op(name, [d, labels[v] & 0xFF]))
        elif op.name.upper() == "SETHI" and is_symbol(op.args[1]):
            d, v = op.args
            name = copy_token("SETHI", op.name)
            nprogram.append(Op(name, [d, labels[v] >> 8]))
        elif op.name.upper() in ("LABEL", "DLABEL", "CONSTANT"):
            continue
        else:
            nprogram.append(op)
    return nprogram


def get_labels(program):
    """Return a dictionary mapping all labels and constants to their values."""
    labels = {}
    pc = 0
    dc = HERA_DATA_START
    for op in program:
        opname = op.name.lower()
        if opname == "label":
            labels[op.args[0]] = pc
        elif opname == "dlabel":
            labels[op.args[0]] = dc
        elif opname == "constant":
            labels[op.args[0]] = op.args[1]
        elif opname == "integer":
            dc += 1
        elif opname == "dskip":
            dc += op.args[0]
        elif opname == "lp_string":
            dc += len(op.args[0]) + 1
        else:
            pc += 1
    return labels


def convert(op):
    """Convert a pseudo-instruction into a list of real instructions."""
    if op.name == "SET":
        return convert_set(*op.args)
    elif op.name == "CMP":
        return [Op("FON", [8]), Op("SUB", ["R0", op.args[0], op.args[1]])]
    elif op.name == "CON":
        return [Op("FON", [8])]
    elif op.name == "COFF":
        return [Op("FOFF", [8])]
    elif op.name == "CBON":
        return [Op("FON", [16])]
    elif op.name == "CCBOFF":
        return [Op("FOFF", [24])]
    elif op.name == "MOVE":
        return [Op("OR", [op.args[0], op.args[1], "R0"])]
    elif op.name == "SETRF":
        return convert_set(*op.args) + convert(Op("FLAGS", [op.args[0]]))
    elif op.name == "FLAGS":
        return [Op("FOFF", [8]), Op("ADD", ["R0", op.args[0], "R0"])]
    elif op.name == "HALT":
        return [Op("BRR", [0])]
    elif op.name == "NOP":
        return [Op("BRR", [1])]
    elif op.name == "CALL":
        return convert_call(*op.args)
    elif op.name == "NEG":
        return [Op("FON", [8]), Op("SUB", [op.args[0], "R0", op.args[1]])]
    elif op.name == "NOT":
        return [
            Op("SETLO", ["R11", 0xFF]),
            Op("SETHI", ["R11", 0xFF]),
            Op("XOR", [op.args[0], "R11", op.args[1]]),
        ]
    else:
        return [op]


def convert_set(d, v):
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


def convert_call(a, l):
    if is_symbol(l):
        return [
            Op("SETLO", ["R13", l]),
            Op("SETHI", ["R13", l]),
            Op("CALL", [a, "R13"]),
        ]
    else:
        return [Op("CALL", [a, l])]


# Constants to pass to verify_base
REGISTER = "r"
REGISTER_OR_LABEL = "rl"
STRING = "s"
U4 = range(0, 2 ** 4)
U5 = range(0, 2 ** 5)
U16 = range(0, 2 ** 16)
I8 = range(-2 ** 7, 2 ** 8)
I16 = range(-2 ** 15, 2 ** 16)


_params_map = {
    "SET": (REGISTER, I16),
    "SETLO": (REGISTER, I8),
    "SETHI": (REGISTER, I8),
    "AND": (REGISTER, REGISTER, REGISTER),
    "OR": (REGISTER, REGISTER, REGISTER),
    "ADD": (REGISTER, REGISTER, REGISTER),
    "SUB": (REGISTER, REGISTER, REGISTER),
    "MUL": (REGISTER, REGISTER, REGISTER),
    "XOR": (REGISTER, REGISTER, REGISTER),
    "INC": (REGISTER, range(1, 65)),
    "DEC": (REGISTER, range(1, 65)),
    "LSL": (REGISTER, REGISTER),
    "LSR": (REGISTER, REGISTER),
    "LSL8": (REGISTER, REGISTER),
    "LSR8": (REGISTER, REGISTER),
    "ASL": (REGISTER, REGISTER),
    "ASR": (REGISTER, REGISTER),
    "SAVEF": (REGISTER,),
    "RSTRF": (REGISTER,),
    "FON": (U4,),
    "FOFF": (U4,),
    "FSET5": (U4,),
    "FSET4": (U4,),
    "LOAD": (REGISTER, U5, REGISTER),
    "STORE": (REGISTER, U5, REGISTER),
    "CALL": (REGISTER, REGISTER_OR_LABEL),
    "RETURN": (REGISTER, REGISTER_OR_LABEL),
}


def verify_args(name, expected, got):
    """Verify that the given args match the expected ones and raise a HERAError 
    otherwise. `name` is the name of the HERA op. `expected` is a tuple or list of 
    constants (REGISTER, U16, etc., defined above) representing the expected argument 
    types to the operation. `args` is a tuple or list of the actual arguments given.
    """
    if len(got) < len(expected):
        raise HERAError("too few args to {} (expected {})".format(name, len(expected)))

    if len(expected) < len(got):
        raise HERAError("too many args to {} (expected {})".format(name, len(expected)))

    ordinals = ["first", "second", "third"]
    for ordinal, pattern, arg in zip(ordinals, expected, got):
        prefix = "{} arg to {} ".format(ordinal, name)
        error = verify_one_arg(pattern, arg)
        if error:
            raise HERAError(prefix + error, line=arg.line, column=arg.column)


def verify_one_arg(pattern, arg):
    """Verify that the argument matches the pattern. Return a string stating the error
    if it doesn't, return None otherwise.
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
            "unknown pattern in hera.preprocessor.verify_one_arg", pattern
        )


def copy_token(val, otkn):
    return Token(otkn.type, val, line=otkn.line, column=otkn.column)


def is_symbol(s):
    return isinstance(s, Token) and s.type == "SYMBOL"
