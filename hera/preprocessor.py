"""Preprocess HERA programs to convert pseudo-instructions and resolve labels.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from typing import Dict, List

from .data import Op, Token, State
from .utils import is_symbol, RELATIVE_BRANCHES


def preprocess(
    program: List[Op], symbol_table: Dict[str, int], state=State()
) -> List[Op]:
    """Preprocess the program into valid input for the exec_many method on the
    VirtualMachine class.

    This function does the following
        - Replaces pseudo-instructions with real ones.
        - Resolves labels into their line numbers.

    The program must be type-checked before being passed to this function.
    """
    nprogram = []
    for op in program:
        if op.name in RELATIVE_BRANCHES and is_symbol(op.args[0]):
            pc = len(nprogram)
            target = symbol_table[op.args[0]]
            jump = target - pc
            if jump < -128 or jump >= 128:
                state.error("label is too far for a relative branch", loc=op.args[0])
            else:
                op.args[0] = jump
        else:
            op = substitute_label(op, symbol_table)

        for new_op in op.convert():
            new_op.loc = op.loc
            new_op.original = op
            nprogram.append(new_op)
    return nprogram


def substitute_label(op: Op, symbol_table: Dict[str, int]) -> Op:
    """Substitute any label in the instruction with its concrete value."""
    for i, arg in enumerate(op.args):
        if isinstance(arg, Token) and arg.type == "SYMBOL":
            op.args[i] = symbol_table[arg]
    return op
