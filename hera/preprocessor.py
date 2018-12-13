"""Preprocess HERA programs to convert pseudo-instructions and resolve labels.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
from lark import Token

from .parser import Op
from .utils import copy_token, emit_error, is_symbol, to_u16


# Arbitrary value copied over from HERA-C.
HERA_DATA_START = 16743


def preprocess(program):
    """Preprocess the program (a list of Op objects) into valid input for the
    exec_many method on the VirtualMachine class.

    This function does the following
        - Replaces pseudo-instructions with real ones.
        - Resolves labels into their line numbers.
    """
    program = [op for old_op in program for op in convert(old_op)]

    labels = get_labels(program)

    program = [substitute_label(op, labels) for op in program]
    program = [op for op in program if op.name not in ("LABEL", "DLABEL", "CONSTANT")]

    return program


def substitute_label(op, labels):
    """Substitute any label in the instruction with its concrete value."""
    if op.name == "SETLO" and is_symbol(op.args[1]):
        d, v = op.args
        name = copy_token("SETLO", op.name)
        try:
            label = labels[v]
        except KeyError:
            emit_error(
                "undefined symbol `{}`".format(v), line=op.name.line, column=v.column
            )
        else:
            return Op(name, [d, label & 0xFF])
    elif op.name == "SETHI" and is_symbol(op.args[1]):
        d, v = op.args
        name = copy_token("SETHI", op.name)
        return Op(name, [d, labels[v] >> 8])
    else:
        return op


def get_labels(program):
    """Return a dictionary mapping all labels and constants to their values."""
    labels = {}
    pc = 0
    dc = HERA_DATA_START
    for op in program:
        odc = dc
        if op.name == "LABEL":
            labels[op.args[0]] = pc
        elif op.name == "DLABEL":
            labels[op.args[0]] = dc
        elif op.name == "CONSTANT":
            labels[op.args[0]] = op.args[1]
        elif op.name == "INTEGER":
            dc += 1
        elif op.name == "DSKIP":
            dc += op.args[0]
        elif op.name == "LP_STRING":
            dc += len(op.args[0]) + 1
        else:
            pc += 1

        if dc >= 0xFFFF and odc < 0xFFFF:
            emit_error("past the end of available memory", line=op.name.line)
    return labels


def convert(op):
    """Convert a pseudo-instruction into a list of real instructions."""
    if op.name.startswith("B") and is_symbol(op.args[0]):
        l = op.args[0]
        new_ops = [
            Op("SETLO", ["R11", l]),
            Op("SETHI", ["R11", l]),
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
