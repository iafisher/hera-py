"""Convenient interface for parsing, type-checking and optionally preprocessing a HERA
file.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import sys
from typing import Dict, List, Tuple

from . import config
from .data import HERAError, Op, State
from .parser import parse
from .preprocessor import preprocess
from .typechecker import typecheck
from .utils import emit_error, print_message_with_location, read_file


def load_program(text: str, state=State()) -> Tuple[List[Op], Dict[str, int]]:
    """Parse the string into a program, type-check it, and preprocess it. A tuple
    (ops, symbol_table) is returned.

    The return value of this function is valid input to the VirtualMachine.exec_many
    method.
    """
    config.ERRORS.clear()
    program = parse(text, includes=True, state=state)
    handle_errors()
    return _load_program_common(program, "<string>", state)


def load_program_from_file(path: str, state=State()) -> Tuple[List[Op], Dict[str, int]]:
    """Convenience function to a read a file and then invoke `load_program_from_str` on
    its contents.
    """
    config.ERRORS.clear()
    if path == "-":
        try:
            text = sys.stdin.read()
        except (IOError, KeyboardInterrupt):
            print()
            sys.exit(3)
        else:
            # So that the program and its output are visually separate.
            print()
    else:
        try:
            text = read_file(path)
        except HERAError as e:
            emit_error(str(e))
    handle_errors()

    program = parse(text, path=path, state=state)
    handle_errors()

    return _load_program_common(program, path, state)


def _load_program_common(program, path, state):
    symbol_table = typecheck(program, state=state)
    handle_errors()

    program = preprocess(program, symbol_table, state=state)
    handle_errors()

    return program, symbol_table


def handle_errors():
    for msg, loc in config.ERRORS:
        msg = config.ANSI_RED_BOLD + "Error" + config.ANSI_RESET + ": " + msg
        print_message_with_location(msg, loc=loc)

    if config.ERRORS:
        config.ERRORS.clear()
        sys.exit(3)
