"""Convenient interface for parsing, type-checking and optionally preprocessing a HERA
file.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import sys
from typing import Dict, List, Tuple

from .data import Op
from .parser import parse, read_file
from .preprocessor import preprocess
from .symtab import get_symbol_table
from .typechecker import typecheck


def load_program(text: str) -> Tuple[List[Op], Dict[str, int]]:
    """Parse the string into a program, type-check it, and preprocess it. A tuple
    (ops, symbol_table) is returned.

    The return value of this function is valid input to the VirtualMachine.exec_many
    method.
    """
    program = parse(text, includes=True)
    return _load_program_common(program, "<string>")


def load_program_from_file(path: str) -> Tuple[List[Op], Dict[str, int]]:
    """Convenience function to a read a file and then invoke `load_program_from_str` on
    its contents.
    """
    text = read_file(path, allow_stdin=True)
    program = parse(text, path=path)
    return _load_program_common(program, path)


def _load_program_common(program, path):
    # Print a newline if the program came from standard input, so that the
    # program and its output are visually separate.
    if path == "-":
        print()

    symbol_table = get_symbol_table(program)
    if symbol_table is None:
        sys.exit(3)

    if not typecheck(program, symbol_table):
        sys.exit(3)
    program = preprocess(program, symbol_table)

    return program, symbol_table
