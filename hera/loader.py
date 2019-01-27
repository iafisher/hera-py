"""Convenient interface for parsing, type-checking and optionally preprocessing a HERA
file.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import sys
from typing import Dict, List, Tuple

from .checker import check
from .data import HERAError, Messages, Op
from .parser import parse
from .utils import handle_messages, read_file


def load_program(text: str, state) -> Tuple[List[Op], Dict[str, int]]:
    """Parse the string into a program, type-check it, and preprocess it. A tuple
    (ops, symbol_table) is returned.

    The return value of this function is valid input to the VirtualMachine.exec_many
    method.
    """
    oplist = handle_messages(state, parse(text, state=state))
    return handle_messages(state, check(oplist, state))


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
            handle_messages(state, Messages(str(e)))

    oplist = handle_messages(state, parse(text, path=path, state=state))
    return handle_messages(state, check(oplist, state))
