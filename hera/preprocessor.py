"""Preprocess HERA programs to convert pseudo-instructions and resolve labels.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from typing import Dict, List

from .data import Op, Token
from .utils import is_symbol, REGISTER_BRANCHES, to_u16


def preprocess(program: List[Op], symbol_table: Dict[str, int]) -> List[Op]:
    """Preprocess the program  into valid input for the exec_many method on the
    VirtualMachine class.

    This function does the following
        - Replaces pseudo-instructions with real ones.
        - Resolves labels into their line numbers.
    """
    program = [substitute_label(op, symbol_table) for op in program]
    program = [
        op._replace(original=old_op) for old_op in program for op in convert(old_op)
    ]
    program = [op for op in program if op.name not in ("LABEL", "DLABEL", "CONSTANT")]
    return program


def substitute_label(op: Op, symbol_table: Dict[str, int]) -> Op:
    """Substitute any label in the instruction with its concrete value."""
    for i, arg in enumerate(op.args):
        if isinstance(arg, Token) and arg.type == "SYMBOL":
            op.args[i] = symbol_table[arg]
    return op


def convert(op: Op) -> List[Op]:
    """Convert a pseudo-instruction into a list of real instructions."""
    if op.name in REGISTER_BRANCHES and isinstance(op.args[0], int):
        lbl = op.args[0]
        new_ops = [
            Op("SETLO", ["R11", lbl & 0xFF]),
            Op("SETHI", ["R11", lbl >> 8]),
            Op(op.name, ["R11"]),
        ]
    elif op.name in REGISTER_BRANCHES and is_symbol(op.args[0]):
        # This clause is only necessary for the symbol table generator--see the note in
        # `convert_call` below.
        lbl = op.args[0]
        new_ops = [
            Op("SETLO", ["R11", lbl]),
            Op("SETHI", ["R11", lbl]),
            Op(op.name, ["R11"]),
        ]
    elif op.name == "SET":
        new_ops = convert_set(*op.args)
    elif op.name == "CMP":
        new_ops = [Op("FON", [8]), Op("SUB", ["R0", op.args[0], op.args[1]])]
    elif op.name == "CON":
        new_ops = [Op("FON", [8])]
    elif op.name == "COFF":
        new_ops = [Op("FOFF", [8])]
    elif op.name == "CBON":
        new_ops = [Op("FON", [16])]
    elif op.name == "CCBOFF":
        new_ops = [Op("FOFF", [24])]
    elif op.name == "MOVE":
        new_ops = [Op("OR", [op.args[0], op.args[1], "R0"])]
    elif op.name == "SETRF":
        new_ops = convert_set(*op.args) + convert(Op("FLAGS", [op.args[0]]))
    elif op.name == "FLAGS":
        new_ops = [Op("FOFF", [8]), Op("ADD", ["R0", op.args[0], "R0"])]
    elif op.name == "HALT":
        new_ops = [Op("BRR", [0])]
    elif op.name == "NOP":
        new_ops = [Op("BRR", [1])]
    elif op.name == "CALL":
        new_ops = convert_call(*op.args)
    elif op.name == "NEG":
        new_ops = [Op("FON", [8]), Op("SUB", [op.args[0], "R0", op.args[1]])]
    elif op.name == "NOT":
        new_ops = [
            Op("SETLO", ["R11", 0xFF]),
            Op("SETHI", ["R11", 0xFF]),
            Op("XOR", [op.args[0], "R11", op.args[1]]),
        ]
    else:
        new_ops = [op]
    # Copy over the line and column information from the original token.
    return [Op(copy_token(new_op.name, op.name), new_op.args) for new_op in new_ops]


def convert_set(d, v):
    if isinstance(v, int):
        v = to_u16(v)
        lo = v & 0xFF
        hi = v >> 8
        return [Op("SETLO", [d, lo]), Op("SETHI", [d, hi])]
    else:
        return [Op("SETLO", [d, v]), Op("SETHI", [d, v])]


def convert_call(a, l):
    if isinstance(l, int):
        return [
            Op("SETLO", ["R13", l & 0xFF]),
            Op("SETHI", ["R13", l >> 8]),
            Op("CALL", [a, "R13"]),
        ]
    elif is_symbol(l):
        # This clause is only necessary for when the symbol table generator calls
        # `convert` to calculate the values of labels in the final program. At that
        # point, labels have not yet been resolved, but we want to make sure we generate
        # the same number of instructions so that the label offsets are correct.
        return [
            Op("SETLO", ["R13", l]),
            Op("SETHI", ["R13", l]),
            Op("CALL", [a, "R13"]),
        ]
    else:
        return [Op("CALL", [a, l])]


def copy_token(val, otkn):
    """Convert the string `val` into a Token with the same line and column numbers as
    `otkn`.
    """
    if isinstance(otkn, Token):
        return Token(otkn.type, val, loc=otkn.location)
    else:
        return val
