"""Type-check HERA programs.

`typecheck` is the public interface of this module.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from typing import Dict, List

from .data import Op, Token
from .utils import (
    DATA_STATEMENTS,
    emit_error,
    is_symbol,
    register_to_index,
    RELATIVE_BRANCHES,
)


def typecheck(program: List[Op], symtab: Dict[str, int]) -> True:
    """Type-check the program and emit errors as appropriate. Return True if the
    program is well-typed.
    """
    error_free = True
    current_file = None
    end_of_data = False
    for op in program:
        # Reset the end_of_data flag whenever an op from a new file is encountered.
        if isinstance(op.name, Token) and op.name.location is not None:
            if current_file is None:
                current_file = op.name.location.path
            else:
                if current_file != op.name.location.path:
                    end_of_data = False
                    current_file = op.name.location.path

        if not end_of_data:
            if op.name not in DATA_STATEMENTS:
                end_of_data = True
        else:
            if op.name in DATA_STATEMENTS:
                emit_error("data statement after instruction", loc=op.name.location)
                error_free = False

        if not typecheck_one(op, symtab):
            error_free = False

        if op.name in RELATIVE_BRANCHES:
            if len(op.args) == 1 and is_symbol(op.args[0]):
                msg = "relative branches cannot use labels"
                msg += " (why not use {} instead?)".format(op.name[:-1])
                emit_error(msg, loc=op.args[0].location)
                error_free = False

    return error_free


def typecheck_one(op: Op, symtab: Dict[str, int]) -> bool:
    """Type-check a single HERA operation and emit error messages as appropriate. Return
    True if no errors were detected.
    """
    params = _types_map.get(op.name)
    if params is not None:
        return check_types(op.name, params, op.args, symtab)
    else:
        emit_error("unknown instruction `{}`".format(op.name), loc=op.name.location)
        return False


def check_types(name, expected, got, symtab):
    """Verify that the given args match the expected ones and emit error messages as
    appropriate. Return True if no errors were detected.

    `name` is the name of the HERA op, as a Token object. `expected` is a
    tuple or list of constants (REGISTER, U16, etc., defined above) representing the
    expected argument types to the operation. `args` is a tuple or list of the actual
    arguments given.
    """
    errors = False

    if len(got) < len(expected):
        emit_error(
            "too few args to {} (expected {})".format(name, len(expected)),
            loc=name.location,
        )
        errors = True

    if len(expected) < len(got):
        emit_error(
            "too many args to {} (expected {})".format(name, len(expected)),
            loc=name.location,
        )
        errors = True

    ordinals = ["first", "second", "third"]
    for ordinal, pattern, arg in zip(ordinals, expected, got):
        prefix = "{} arg to {} ".format(ordinal, name)
        error_msg = check_one_type(pattern, arg, symtab)
        if error_msg:
            emit_error(prefix + error_msg, loc=arg.location)
            errors = True

    return not errors


def check_one_type(pattern, arg, symtab):
    """Verify that the argument matches the pattern. Return a string stating the error
    if it doesn't, return None otherwise.
    """
    # TODO: Overengineered?
    if pattern == REGISTER:
        if not isinstance(arg, Token) or arg.type != "REGISTER":
            return "not a register"

        if arg.lower() == "pc":
            return "program counter cannot be accessed or changed directly"

        try:
            register_to_index(arg)
        except ValueError:
            return "not a valid register"
    elif pattern == REGISTER_OR_LABEL:
        if not isinstance(arg, Token):
            return "not a register or label"

        if arg.type == "REGISTER":
            if arg.lower() == "pc":
                return "program counter cannot be accessed or changed directly"

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
    # Interrupt processing
    "SWI": (U4,),
    "RTI": (),
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
    # Debugging instructions
    "print_reg": (REGISTER,),
    "print": (STRING,),
    "println": (STRING,),
}
