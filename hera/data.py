"""Some important data structures for the HERA interpreter.

Location objects represent a location in a file, for the use of warnings and error
messages. The `file_lines` field is a pointer to a list of lines in the file, so that
the actual line can be printed in the message.

Op objects represent HERA operations.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
from collections import namedtuple
from typing import Optional, Tuple


DEFAULT_DATA_START = 0xC001


class State:
    """The global state of the interpreter."""

    # TODO: Rename to Settings?

    def __init__(self):
        self.color = True
        self.data_start = DEFAULT_DATA_START
        self.warning_count = 0
        self.warned_for_octal = False


Location = namedtuple("Location", ["line", "column", "path", "file_lines"])


class Op(namedtuple("Op", ["name", "args", "original"])):
    def __new__(cls, name, args, original=None):
        return tuple.__new__(cls, (name, args, original))

    def __eq__(self, other):
        return (
            isinstance(other, Op)
            and self.name == other.name
            and self.args == other.args
        )

    def __repr__(self):
        orepr = "None" if self.original is None else "Op(...)"
        return "Op(name={!r}, args={!r}, original={})".format(
            self.name, self.args, orepr
        )


Program = namedtuple("Program", ["data", "code", "symbol_table"])


class IntToken(int):
    def __new__(cls, value, loc=None, **kwargs):
        self = super(IntToken, cls).__new__(cls, value, **kwargs)
        self.location = loc
        return self


class Token(str):
    def __new__(cls, type_, value, loc=None):
        self = super(Token, cls).__new__(cls, value)
        self.type = type_
        self.location = loc
        return self


class Messages:
    def __init__(self, msg=None, loc=None, *, warning=False):
        self.errors = []
        self.warnings = []
        if msg is not None:
            if warning:
                self.warnings.append((msg, loc))
            else:
                self.errors.append((msg, loc))

    def extend(self, messages):
        self.errors.extend(messages.errors)
        self.warnings.extend(messages.warnings)
        return self

    def err(self, msg, loc=None):
        self.errors.append((msg, loc))

    def warn(self, msg, loc=None):
        self.warnings.append((msg, loc))


ErrorType = Tuple[str, Optional[Location]]


class HERAError(Exception):
    pass


class Constant(int):
    pass


class Label(int):
    pass


class DataLabel(int):
    pass
