"""
Convenient interface for parsing, type-checking and preprocessing a HERA program
contained in a string or file.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: March 2019
"""
from .checker import check
from .data import Program, Settings
from .parser import parse
from .utils import handle_messages, Path, PATH_STRING, read_file_or_stdin


def load_program(text: Path, settings=Settings()) -> Program:
    """
    Parse the string into a program, type-check it, and preprocess it.

    The return value of this function is valid input to the VirtualMachine.run method.
    """
    oplist, parse_messages = parse(text, path=PATH_STRING, settings=settings)
    program, check_messages = check(oplist, settings=settings)
    handle_messages(settings, parse_messages.extend(check_messages))
    return program


def load_program_from_file(path: Path, settings=Settings()) -> Program:
    """
    Convenience function to a read a file and then invoke `load_program_from_str` on its
    contents.
    """
    text = read_file_or_stdin(path, settings)
    oplist, parse_messages = parse(text, path=path, settings=settings)
    program, check_messages = check(oplist, settings=settings)
    handle_messages(settings, parse_messages.extend(check_messages))
    return program
