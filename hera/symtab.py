"""Create symbol tables from HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from typing import Dict, List, Tuple

from .config import HERA_DATA_START
from .data import Op
from .utils import emit_error, is_symbol, REGISTER_BRANCHES


# IDEA: convert_constants method.


def get_symbol_table(program: List[Op]) -> Tuple[Dict[str, int], bool]:
    """Return the program's symbol table, a dictionary mapping from strings to Label,
    DataLabel and Constant objects (all subclasses of int).

    Return value is (symbol_table, errors).
    """
    errors = False
    symbol_table = {}  # type: Dict[str, int]
    pc = 0
    dc = HERA_DATA_START
    for op in program:
        odc = dc
        if op.name == "LABEL":
            if len(op.args) == 1:
                symbol_table[op.args[0]] = Label(pc)
        elif op.name == "DLABEL":
            if len(op.args) == 1:
                if dc >= 0xFFFF:
                    # If the data counter is greater than 0xFFFF, then it's invalid
                    # and type-checking will fail, so we don't want to put its actual
                    # value in the symbol table in case, e.g SET(R1, DATA) is used later
                    # and an out-of-range error would occur because 0xFFFF and higher
                    # values don't fit into 16 bits.
                    symbol_table[op.args[0]] = DataLabel(0)
                else:
                    symbol_table[op.args[0]] = DataLabel(dc)
        elif op.name == "CONSTANT":
            if len(op.args) == 2:
                try:
                    c = Constant(op.args[1])
                except ValueError:
                    continue

                if c >= 0xFFFF or c < -32768:
                    c = 0

                symbol_table[op.args[0]] = Constant(c)
        elif op.name == "INTEGER":
            dc += 1
        elif op.name == "DSKIP":
            if len(op.args) == 1:
                if isinstance(op.args[0], int):
                    dc += op.args[0]
                elif op.args[0] in symbol_table:
                    if isinstance(symbol_table[op.args[0]], Constant):
                        dc += symbol_table[op.args[0]]
        elif op.name == "LP_STRING":
            if len(op.args) == 1 and isinstance(op.args[0], str):
                dc += len(op.args[0]) + 1
        else:
            # IDEA: Don't even need a concrete value for pc here, can calculate
            # it later.
            pc += operation_length(op)

        if dc >= 0xFFFF and odc < 0xFFFF:
            emit_error("past the end of available memory", loc=op.name)
            errors = True

    return symbol_table, errors


class Label(int):
    pass


class DataLabel(int):
    pass


class Constant(int):
    pass


def operation_length(op):
    # TODO: Better name.
    if op.name in REGISTER_BRANCHES:
        return 3
    elif op.name == "SET":
        return 2
    elif op.name == "CMP":
        return 2
    elif op.name == "SETRF":
        return 4
    elif op.name == "FLAGS":
        return 2
    elif op.name == "CALL":
        if len(op.args) == 2 and isinstance(op.args[1], int) or is_symbol(op.args[1]):
            return 3
        else:
            return 1
    elif op.name == "NEG":
        return 2
    elif op.name == "NOT":
        return 3
    else:
        return 1
