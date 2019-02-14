"""Some important data structures for the HERA interpreter.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
from collections import namedtuple


DEFAULT_DATA_START = 0xC001

VOLUME_QUIET = "quiet"
VOLUME_NORMAL = "normal"
VOLUME_VERBOSE = "verbose"


class Settings:
    """Global settings of the interpreter."""

    def __init__(self, *, color=True, mode="", volume=VOLUME_NORMAL):
        self.allow_interrupts = False
        self.code = False
        self.color = color
        self.data = False
        self.data_start = DEFAULT_DATA_START
        self.mode = mode
        self.no_debug_ops = False
        self.path = None
        self.stdout = False
        self.warn_octal_on = True
        self.warn_return_on = True
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


Program = namedtuple("Program", ["data", "code", "symbol_table", "debug_info"])
DebugInfo = namedtuple("DebugInfo", ["labels"])


class Token:
    # Possible values for the `type` field.
    INT = "TOKEN_INT"
    REGISTER = "TOKEN_REGISTER"
    SYMBOL = "TOKEN_SYMBOL"
    STRING = "TOKEN_STRING"
    BRACKETED = "TOKEN_BRACKETED"
    CHAR = "TOKEN_CHAR"
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
    ERROR = "TOKEN_ERROR"
    UNKNOWN = "TOKEN_UNKNOWN"

    def __init__(self, type_, value, location=None):
        self.type = type_
        self.value = value
        self.location = location

    @classmethod
    def R(cls, i, location=None):
        return cls(cls.REGISTER, i, location)

    @classmethod
    def Int(cls, x, location=None):
        return cls(cls.INT, x, location)

    @classmethod
    def Sym(cls, s, location=None):
        return cls(cls.SYMBOL, s, location)

    def __eq__(self, other):
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        else:
            return self.value == other

    def __repr__(self):
        return "Token({0.type!r}, {0.value!r}, loc={0.location!r})".format(self)


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


class HERAError(Exception):
    pass


class Constant(int):
    pass


class Label(int):
    pass


class DataLabel(int):
    pass
