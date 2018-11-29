"""Type-check HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
from lark import Token

from .utils import is_symbol, register_to_index, HERAError


def typecheck(program):
    for op in program:
        params = _types_map.get(op.name)
        if params is None and op.name.upper().startswith("B"):
            if op.name.upper().endswith("R") and len(op.name) > 2:
                params = (I8,)
            else:
                params = (REGISTER_OR_LABEL,)
        if params is not None:
            try:
                check_types(op.name, params, op.args)
            except HERAError as e:
                # Fill in line number if not already present.
                if not e.line:
                    e.line = op.name.line
                raise e


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
    "FON": (U4,),
    "FOFF": (U4,),
    "FSET5": (U4,),
    "FSET4": (U4,),
    "LOAD": (REGISTER, U5, REGISTER),
    "STORE": (REGISTER, U5, REGISTER),
    "CALL": (REGISTER, REGISTER_OR_LABEL),
    "RETURN": (REGISTER, REGISTER_OR_LABEL),
}


def check_types(name, expected, got):
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
        error = check_one_type(pattern, arg)
        if error:
            raise HERAError(prefix + error, line=arg.line, column=arg.column)


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
