"""Create symbol tables from HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from typing import Dict, List

from .config import HERA_DATA_START
from .data import Op
from .preprocessor import convert
from .utils import emit_error


def get_symbol_table(program: List[Op]) -> Dict[str, int]:
    """Return the program's symbol table, a dictionary mapping from strings to Label,
    DataLabel and Constant objects (all subclasses of int).
    """
    symbol_table = {}  # type: Dict[str, int]
    pc = 0
    dc = HERA_DATA_START
    for op in program:
        odc = dc
        if op.name == "LABEL":
            if len(op.args) == 1:
                update_symbol_table(symbol_table, op.args[0], Label(pc), op)
        elif op.name == "DLABEL":
            if len(op.args) == 1:
                update_symbol_table(symbol_table, op.args[0], DataLabel(dc), op)
        elif op.name == "CONSTANT":
            if len(op.args) == 2:
                update_symbol_table(symbol_table, op.args[0], Constant(op.args[1]), op)
        elif op.name == "INTEGER":
            dc += 1
        elif op.name == "DSKIP":
            if len(op.args) == 1:
                if isinstance(op.args[0], int):
                    dc += op.args[0]
                elif op.args[0] in symbol_table and isinstance(
                    symbol_table[op.args[0]], Constant
                ):
                    dc += symbol_table[op.args[0]]
        elif op.name == "LP_STRING":
            if len(op.args) == 1 and isinstance(op.args[0], str):
                dc += len(op.args[0]) + 1
        else:
            # IDEA: Instead of using the convert function (which introduces undesirable
            # coupling between this module and the preprocessor), write a function to
            # calculate this value directly.
            #
            # This has the disadvantage of duplicating some of the logic of conversion
            # though.
            pc += len(convert(op))

        if dc >= 0xFFFF and odc < 0xFFFF:
            emit_error("past the end of available memory", loc=op.name.location)

    return symbol_table


def update_symbol_table(symbol_table: Dict[str, int], k: str, v: int, op: Op) -> None:
    if k in symbol_table:
        emit_error(
            "symbol `{}` has already been defined".format(k), loc=op.name.location
        )
    else:
        symbol_table[k] = v


class Label(int):
    pass


class DataLabel(int):
    pass


class Constant(int):
    pass
