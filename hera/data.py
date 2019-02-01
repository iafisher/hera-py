"""Some important data structures for the HERA interpreter.

Location objects represent a location in a file, for the use of warnings and error
messages. The `file_lines` field is a pointer to a list of lines in the file, so that
the actual line can be printed in the message.

Op objects represent HERA operations.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
from collections import namedtuple
from enum import Enum
from typing import Optional, Tuple


DEFAULT_DATA_START = 0xC001

VOLUME_QUIET = "quiet"
VOLUME_NORMAL = "normal"
VOLUME_VERBOSE = "verbose"


class Settings:
    """Global settings of the interpreter."""

    def __init__(
        self,
        *,
        color=True,
        data_start=DEFAULT_DATA_START,
        no_debug=False,
        volume=VOLUME_NORMAL,
        warn_octal_on=True,
        warn_return_on=True
    ):
        self.color = color
        self.data_start = data_start
        self.no_debug = no_debug
        self.warn_octal_on = warn_octal_on
        self.warn_return_on = warn_return_on
        self.volume = volume
        self.warning_count = 0


class Location(namedtuple("Location", ["line", "column", "path", "file_lines"])):
    def __repr__(self):
        if self.file_lines:
            return "Location(line={}, column={}, path={!r}, file_lines=[...])".format(
                self.line, self.column, self.path
            )
        else:
            return "Location(line={}, column={}, path={!r}, file_lines=[])".format(
                self.line, self.column, self.path
            )


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

    def __repr__(self):
        return "Token({!r}, {}, loc={})".format(
            self.type, super().__repr__(), self.location
        )


class TOKEN(Enum):
    """Enumeration for the type field of Token objects."""

    # Values
    INT = "TOKEN_INT"
    REGISTER = "TOKEN_REGISTER"
    SYMBOL = "TOKEN_SYMBOL"
    STRING = "TOKEN_STRING"
    BRACKETED = "TOKEN_BRACKETED"
    CHAR = "TOKEN_CHAR"

    # Operators
    MINUS = "TOKEN_MINUS"
    AT = "TOKEN_AT"
    ASTERISK = "TOKEN_ASTERISK"
    PLUS = "TOKEN_PLUS"
    SLASH = "TOKEN_SLASH"

    LPAREN = "TOKEN_LPAREN"
    RPAREN = "TOKEN_RPAREN"
    LBRACE = "TOKEN_LBRACE"
    RBRACE = "TOKEN_RBRACE"
    COMMA = "TOKEN_COMMA"
    SEMICOLON = "TOKEN_SEMICOLON"

    FMT = "TOKEN_FMT"
    INCLUDE = "TOKEN_INCLUDE"
    EOF = "TOKEN_EOF"
    UNKNOWN = "TOKEN_UNKNOWN"


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
