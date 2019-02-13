"""The HERA assembler.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
from typing import List, Tuple

from .data import Program


def assemble(program: Program) -> Tuple[List[bytes], List[bytes]]:
    code = []
    data = []

    for op in program.code:
        code.append(op.assemble())

    for data_op in program.data:
        data.append(data_op.assemble())

    return (code, data)
