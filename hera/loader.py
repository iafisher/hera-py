"""Convenient interface for parsing, type-checking and optionally preprocessing a HERA
file.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import sys
from typing import Dict, List, Tuple

from .data import HERAError, Op
from .op import resolve_ops
from .parser import parse
from .preprocessor import preprocess
from .typechecker import typecheck
from .utils import handle_errors, read_file


def load_program(text: str, state) -> Tuple[List[Op], Dict[str, int]]:
    """Parse the string into a program, type-check it, and preprocess it. A tuple
    (ops, symbol_table) is returned.

    The return value of this function is valid input to the VirtualMachine.exec_many
    method.
    """
    program = parse(text, state=state)
    handle_errors(state)
    return _load_program_common(program, "<string>", state)


def load_program_from_file(path: str, state) -> Tuple[List[Op], Dict[str, int]]:
    """Convenience function to a read a file and then invoke `load_program_from_str` on
    its contents.
    """
    if path == "-":
        try:
            text = sys.stdin.read()
        except (IOError, KeyboardInterrupt):
            print(file=sys.stderr)
            sys.exit(3)
        else:
            # So that the program and its output are visually separate.
            print(file=sys.stderr)
    else:
        try:
            text = read_file(path)
        except HERAError as e:
            # TODO
            state.error(str(e))
    handle_errors(state)

    program = parse(text, path=path, state=state)
    handle_errors(state)

    return _load_program_common(program, path, state)


def _load_program_common(program, path, state):
    program = resolve_ops(program, state=state)
    symbol_table = typecheck(program, state=state)
    handle_errors(state)

    program = preprocess(program, symbol_table, state=state)
    handle_errors(state)

    return program, symbol_table
