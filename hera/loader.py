"""Convenient interface for parsing, type-checking and optionally preprocessing a HERA
file.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import sys
from typing import Dict, List, Tuple

from .data import Op
from .parser import parse_file
from .preprocessor import preprocess
from .symtab import get_symbol_table
from .typechecker import typecheck


def load_program(path: str) -> Tuple[List[Op], Dict[str, int]]:
    """Read the HERA program from the file at `path`, parse it, type-check it, and
    preprocess it. A tuple of (program, symbol_table) is returned.

    The return value of this function is valid input to the VirtualMachine.exec_many
    method.
    """
    program = parse_file(path, includes=True, allow_stdin=True)

    # Print a newline if the program came from standard input, so that the
    # program and its output are visually separate.
    if path == "-":
        print()

    symbol_table = get_symbol_table(program)
    if not typecheck(program, symbol_table):
        sys.exit(3)
    program = preprocess(program, symbol_table)

    return program, symbol_table
