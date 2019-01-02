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


def load_program(path: str, *, preprocess=True) -> List[Op]:
    """Read the HERA program from the file at `path` and return the program.

    This function combines parsing, type-checking and preprocessing (if `preprocess` is
    set to True).
    """
    config.ERROR_COUNT = config.WARNING_COUNT = 0

    program = parse_file(path, includes=True, allow_stdin=True)

    # Print a newline if the program came from standard input, so that the
    # program and its output are visually separate.
    if path == "-":
        print()

    symtab = get_symtab(program)

    typecheck(program, symtab)
    if config.ERROR_COUNT > 0:
        sys.exit(3)

    if preprocess:
        program = preprocessor.preprocess(program, symtab)

    return program
