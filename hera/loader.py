"""Convenient interface for parsing, type-checking and optionally preprocessing a HERA
file.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import sys
from typing import List

from . import config, preprocessor
from .data import Op
from .parser import parse_file
from .symtab import get_symtab
from .typechecker import typecheck


def load_program(path: str) -> List[Op]:
    """Read the HERA program from the file at `path`, parse it, type-check it, and
    preprocess it.

    The return value of this function is valid input to the VirtualMachine.exec_many
    method.
    """
    config.WARNING_COUNT = 0

    program = parse_file(path, includes=True, allow_stdin=True)

    # Print a newline if the program came from standard input, so that the
    # program and its output are visually separate.
    if path == "-":
        print()

    symtab = get_symtab(program)
    if not typecheck(program, symtab):
        sys.exit(3)
    program = preprocessor.preprocess(program, symtab)

    return program
