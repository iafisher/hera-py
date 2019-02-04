"""Convenient interface for parsing, type-checking and optionally preprocessing a HERA
file.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import sys
from typing import Dict, Tuple

from .checker import check
from .data import HERAError, Messages, Program, Settings
from .parser import parse
from .utils import handle_messages, read_file


def load_program(text: str, settings=Settings()) -> Tuple[Program, Dict[str, int]]:
    """Parse the string into a program, type-check it, and preprocess it. A tuple
    (ops, symbol_table) is returned.

    The return value of this function is valid input to the VirtualMachine.run method.
    """
    oplist = handle_messages(settings, parse(text, settings=settings))
    return handle_messages(settings, check(oplist, settings))


def load_program_from_file(
    path: str, settings=Settings()
) -> Tuple[Program, Dict[str, int]]:
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

        try:
            text.encode("ascii")
        except UnicodeEncodeError:
            handle_messages(settings, Messages("non-ASCII byte in file."))

        path = "<stdin>"
    else:
        try:
            text = read_file(path)
        except HERAError as e:
            handle_messages(settings, Messages(str(e) + "."))

    oplist = handle_messages(settings, parse(text, path=path, settings=settings))
    return handle_messages(settings, check(oplist, settings))
