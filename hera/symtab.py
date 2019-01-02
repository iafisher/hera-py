"""Create symbol tables from HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from typing import Dict, List

from .data import Op
from .preprocessor import convert
from .utils import emit_error


# Arbitrary value copied over from HERA-C.
HERA_DATA_START = 0xC001


def get_symtab(program: List[Op]) -> Dict[str, int]:
    """Return the program's symbol table, a dictionary mapping from strings to Label,
    DataLabel and Constant objects (all subclasses of int).
    """
    symtab = {}  # type: Dict[str, int]
    pc = 0
    dc = HERA_DATA_START
    for op in program:
        odc = dc
        if op.name == "LABEL":
            if len(op.args) == 1:
                update_labels(symtab, op.args[0], Label(pc), op)
        elif op.name == "DLABEL":
            if len(op.args) == 1:
                update_labels(symtab, op.args[0], DataLabel(dc), op)
        elif op.name == "CONSTANT":
            if len(op.args) == 2:
                update_labels(symtab, op.args[0], Constant(op.args[1]), op)
        elif op.name == "INTEGER":
            dc += 1
        elif op.name == "DSKIP":
            if len(op.args) == 1:
                if isinstance(op.args[0], int):
                    dc += op.args[0]
                elif op.args[0] in symtab and isinstance(symtab[op.args[0]], Constant):
                    dc += symtab[op.args[0]]
        elif op.name == "LP_STRING":
            if len(op.args) == 1 and isinstance(op.args[0], str):
                dc += len(op.args[0]) + 1
        else:
            pc += len(convert(op))

        if dc >= 0xFFFF and odc < 0xFFFF:
            emit_error("past the end of available memory", loc=op.name.location)

    return symtab


def update_labels(labels: Dict[str, int], k: str, v: int, op: Op) -> None:
    if k in labels:
        emit_error(
            "symbol `{}` has already been defined".format(k), loc=op.name.location
        )
    else:
        labels[k] = v


class Label(int):
    pass


class DataLabel(int):
    pass


class Constant(int):
    pass
