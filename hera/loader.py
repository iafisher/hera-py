"""Convenient interface for parsing, type-checking and optionally preprocessing a HERA
file.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
import sys

from . import config, preprocessor
from .parser import parse_file
from .symtab import get_symtab
from .typechecker import typecheck
from .utils import emit_error, HERAError


def load_program(path, *, preprocess=True):
    """Read the HERA program from the file at `path` and return the program represented
    as a list of Op objects.

    This function combines parsing, type-checking and preprocessing (if `preprocess` is
    set to True).
    """
    config.ERROR_COUNT = config.WARNING_COUNT = 0

    try:
        program = parse_file(path, expand_includes=True, allow_stdin=True)
    except HERAError as e:
        emit_error(str(e), loc=e.location, line=e.line, column=e.column, exit=True)
    except (IOError, KeyboardInterrupt):
        print()
        return

    # Print a newline if the program came from standard input, so that the
    # program and its output are visually separate.
    if path == "-":
        print()

    # Filter out #include statements for now.
    program = [op for op in program if op.name != "#include"]

    symtab = get_symtab(program)

    typecheck(program, symtab)
    if config.ERROR_COUNT > 0:
        sys.exit(3)

    if preprocess:
        program = preprocessor.preprocess(program, symtab)
        if config.ERROR_COUNT > 0:
            sys.exit(3)

    return program
