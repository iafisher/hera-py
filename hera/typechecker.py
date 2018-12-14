"""Type-check HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
from lark import Token

from .utils import emit_error, is_symbol, register_to_index


DATA_STATEMENTS = set(["CONSTANT", "DLABEL", "INTEGER", "LP_STRING", "DSKIP"])


def typecheck(program, symtab):
    """Type-check the program and emit errors as appropriate."""
    end_of_data = False
    for op in program:
        if not end_of_data:
            if op.name not in DATA_STATEMENTS:
                end_of_data = True
        else:
            if op.name in DATA_STATEMENTS:
                emit_error("data statement after instruction", line=op.name.line)
        typecheck_one(op, symtab)


def typecheck_one(op, symtab):
    """Type-check a single HERA op and emit errors as appropriate."""
    params = _types_map.get(op.name)
    if params is not None:
        check_types(op.name, params, op.args, symtab)
    else:
        emit_error("unknown instruction `{}`".format(op.name), line=op.name.line)


# Constants to pass to check_types
REGISTER = "r"
REGISTER_OR_LABEL = "rl"
LABEL = "l"
STRING = "s"
U4 = range(0, 2 ** 4)
U5 = range(0, 2 ** 5)
U16 = range(0, 2 ** 16)
I8 = range(-2 ** 7, 2 ** 8)
I16 = range(-2 ** 15, 2 ** 16)


_types_map = {
    # Set and increment instructions
    "SETLO": (REGISTER, I8),
    "SETHI": (REGISTER, I8),
    "INC": (REGISTER, range(1, 65)),
    "DEC": (REGISTER, range(1, 65)),
    # Arithmetic, logical and shift instructions
    "AND": (REGISTER, REGISTER, REGISTER),
    "OR": (REGISTER, REGISTER, REGISTER),
    "ADD": (REGISTER, REGISTER, REGISTER),
    "SUB": (REGISTER, REGISTER, REGISTER),
    "MUL": (REGISTER, REGISTER, REGISTER),
    "XOR": (REGISTER, REGISTER, REGISTER),
    "LSL": (REGISTER, REGISTER),
    "LSR": (REGISTER, REGISTER),
    "LSL8": (REGISTER, REGISTER),
    "LSR8": (REGISTER, REGISTER),
    "ASL": (REGISTER, REGISTER),
    "ASR": (REGISTER, REGISTER),
    # Flag manipulation
    "SAVEF": (REGISTER,),
    "RSTRF": (REGISTER,),
    "FON": (U5,),
    "FOFF": (U5,),
    "FSET5": (U5,),
    "FSET4": (U4,),
    # Memory instructions
    "LOAD": (REGISTER, U5, REGISTER),
    "STORE": (REGISTER, U5, REGISTER),
    # Branch instructions
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
    # Pseudo-instructions
    "SET": (REGISTER, I16),
    "SETRF": (REGISTER, I16),
    "MOVE": (REGISTER, REGISTER),
    "CMP": (REGISTER, REGISTER),
    "NEG": (REGISTER, REGISTER),
    "NOT": (REGISTER, REGISTER),
    "CBON": (),
    "CON": (),
    "COFF": (),
    "CCBOFF": (),
    "FLAGS": (REGISTER,),
    "NOP": (),
    "HALT": (),
    "LABEL": (LABEL,),
    # Data statements
    "CONSTANT": (LABEL, I16),
    "DLABEL": (LABEL,),
    "INTEGER": (I16,),
    "LP_STRING": (STRING,),
    "DSKIP": (U16,),
}


def check_types(name, expected, got, symtab):
    """Verify that the given args match the expected ones and emit errors as
    appropriate. `name` is the name of the HERA op, as a Token object. `expected` is a
    tuple or list of constants (REGISTER, U16, etc., defined above) representing the
    expected argument types to the operation. `args` is a tuple or list of the actual
    arguments given.
    """
    if len(got) < len(expected):
        emit_error(
            "too few args to {} (expected {})".format(name, len(expected)),
            line=name.line,
        )

    if len(expected) < len(got):
        emit_error(
            "too many args to {} (expected {})".format(name, len(expected)),
            line=name.line,
        )

    ordinals = ["first", "second", "third"]
    for ordinal, pattern, arg in zip(ordinals, expected, got):
        prefix = "{} arg to {} ".format(ordinal, name)
        error = check_one_type(pattern, arg, symtab)
        if error:
            emit_error(prefix + error, line=arg.line, column=arg.column)


def check_one_type(pattern, arg, symtab):
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
    elif pattern == LABEL:
        if not isinstance(arg, Token) or arg.type != "SYMBOL":
            return "not a symbol"
    elif pattern == STRING:
        if not isinstance(arg, Token) or arg.type != "STRING":
            return "not a string"
    elif isinstance(pattern, range):
        if is_symbol(arg):
            try:
                arg = symtab[arg]
            except KeyError:
                return "undefined constant"

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
