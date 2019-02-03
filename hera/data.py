"""Some important data structures for the HERA interpreter.


Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
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
    """A class to represent a location in a file, for the use of warnings and error
    messages. The `file_lines` field is a pointer to a list of lines in the file, so
    that the actual line can be printed in the message.
    """

    def __repr__(self):
        if self.file_lines:
            return "Location(line={}, column={}, path={!r}, file_lines=[...])".format(
                self.line, self.column, self.path
            )
        else:
            return "Location(line={}, column={}, path={!r}, file_lines=[])".format(
                self.line, self.column, self.path
            )


Program = namedtuple("Program", ["data", "code", "symbol_table"])


class Token:
    def __init__(self, type_, value, location=None):
        self.type = type_
        self.value = value
        self.location = location

    @classmethod
    def R(cls, i, location=None):
        return cls(TOKEN.REGISTER, i, location)

    @classmethod
    def INT(cls, x, location=None):
        return cls(TOKEN.INT, x, location)

    @classmethod
    def SYM(cls, s, location=None):
        return cls(TOKEN.SYMBOL, s, location)

    @classmethod
    def STR(cls, s, location=None):
        return cls(TOKEN.STRING, s, location)

    def __eq__(self, other):
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        else:
            return self.value == other

    def __repr__(self):
        return "Token({0.type!r}, {0.value!r}, loc={0.location!r})".format(self)


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
