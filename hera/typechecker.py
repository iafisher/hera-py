"""Type-check HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
from collections import namedtuple

from lark import Token

from .utils import is_symbol, register_to_index


ErrorInfo = namedtuple("ErrorInfo", ["msg", "line", "column"])


def typecheck(program):
    """Type-check the program and return a list of errors encountered."""
    errors = []
    for op in program:
        errors.extend(typecheck_one(op))
    return errors


def typecheck_one(op):
    """Type-check a single HERA op and return a list of errors encountered."""
    params = _types_map.get(op.name)
    if params is not None:
        return check_types(op.name, params, op.args)
    else:
        return [ErrorInfo("unknown instruction `{}`".format(op.name), op.name.line, None)]


# Constants to pass to check_types
REGISTER = "r"
REGISTER_OR_LABEL = "rl"
STRING = "s"
U4 = range(0, 2 ** 4)
U5 = range(0, 2 ** 5)
U16 = range(0, 2 ** 16)
I8 = range(-2 ** 7, 2 ** 8)
I16 = range(-2 ** 15, 2 ** 16)


_types_map = {
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
    "FON": (U5,),
    "FOFF": (U5,),
    "FSET5": (U5,),
    "FSET4": (U4,),
    "LOAD": (REGISTER, U5, REGISTER),
    "STORE": (REGISTER, U5, REGISTER),
    "CALL": (REGISTER, REGISTER_OR_LABEL),
    "RETURN": (REGISTER, REGISTER_OR_LABEL),
    "BR": (REGISTER_OR_LABEL,),
    "BRR": (I8,),
    "BL": (REGISTER_OR_LABEL,),
    "BLR": (I8,),
    "BGE": (REGISTER_OR_LABEL,),
    "BGER": (I8,),
    "BLE": (REGISTER_OR_LABEL,),
    "BLER": (I8,),
    "BG": (REGISTER_OR_LABEL,),
    "BGR": (I8,),
    "BULE": (REGISTER_OR_LABEL,),
    "BULER": (I8,),
    "BUG": (REGISTER_OR_LABEL,),
    "BUGR": (I8,),
    "BZ": (REGISTER_OR_LABEL,),
    "BZR": (I8,),
    "BNZ": (REGISTER_OR_LABEL,),
    "BNZR": (I8,),
    "BC": (REGISTER_OR_LABEL,),
    "BCR": (I8,),
    "BNC": (REGISTER_OR_LABEL,),
    "BNCR": (I8,),
    "BS": (REGISTER_OR_LABEL,),
    "BSR": (I8,),
    "BNS": (REGISTER_OR_LABEL,),
    "BNSR": (I8,),
    "BV": (REGISTER_OR_LABEL,),
    "BVR": (I8,),
    "BNV": (REGISTER_OR_LABEL,),
    "BNVR": (I8,),
}


def check_types(name, expected, got):
    """Verify that the given args match the expected ones and return a list of errors.
    `name` is the name of the HERA op, as a Token object. `expected` is a tuple or list
    of constants (REGISTER, U16, etc., defined above) representing the expected argument 
    types to the operation. `args` is a tuple or list of the actual arguments given.
    """
    errors = []

    if len(got) < len(expected):
        errors.append(
            ErrorInfo(
                "too few args to {} (expected {})".format(name, len(expected)),
                name.line,
                None,
            )
        )

    if len(expected) < len(got):
        errors.append(
            ErrorInfo(
                "too many args to {} (expected {})".format(name, len(expected)),
                name.line,
                None,
            )
        )

    ordinals = ["first", "second", "third"]
    for ordinal, pattern, arg in zip(ordinals, expected, got):
        prefix = "{} arg to {} ".format(ordinal, name)
        error = check_one_type(pattern, arg)
        if error:
            errors.append(ErrorInfo(prefix + error, arg.line, arg.column))

    return errors


def check_one_type(pattern, arg):
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
            "unknown pattern in hera.typechecker.check_one_type", pattern
        )
