"""
Definitions of important data structures for hera-py.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
from collections import namedtuple


# The default memory address of the first cell in the data segment.
DEFAULT_DATA_START = 0xC001

VOLUME_QUIET = "quiet"
VOLUME_NORMAL = "normal"
VOLUME_VERBOSE = "verbose"


class Settings:
    """Global settings of the interpreter."""

    def __init__(self, *, color=True, mode="", volume=VOLUME_NORMAL):
        # Are SWI and RTI operations allowed?
        self.allow_interrupts = False
        # Should the assembler print out code?
        self.code = False
        # Is color output enabled?
        self.color = color
        # Should the assembler print out data?
        self.data = False
        # Where is the start of the data segment?
        self.data_start = DEFAULT_DATA_START
        # What is the program's mode (e.g., "debug", "assemble")?
        self.mode = mode
        # Are debugging operations allowed?
        self.no_debug_ops = False
        # Should the preprocessor obfuscate the given code?
        self.obfuscate = False
        # What path was the program invoked on?
        self.path = None
        # Should the assembler print to standard output?
        self.stdout = False
        # Should the interpreter quit after a certain number of operations have been
        # executed?
        self.throttle = False
        # Should warnings be issued for zero-prefixed octal numbers?
        self.warn_octal_on = True
        # Should warnings be issued for un-idiomatic use of the RETURN operation?
        self.warn_return_on = True
        # How loud should the program be?
        self.volume = volume
        # How many warnings have been issued? This isn't a setting, strictly speaking,
        # but it's convenient to attach it to this class.
        self.warning_count = 0


class Location(namedtuple("Location", ["line", "column", "path", "file_lines"])):
    """
    A class to represent a location in a file, for the use of warnings and error
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


# The data structure that represents a HERA program. `data` and `code` are each a list
# of AbstractOperations. `symbol_table` and `debug_info` are for the use of the
# debugger.
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
        # The value may be a string or an integer.
        self.value = value
        self.location = location

    @classmethod
    def R(cls, i, location=None):
        """Construct a register token."""
        return cls(cls.REGISTER, i, location)

    @classmethod
    def Int(cls, x, location=None):
        """Construct an integer token."""
        return cls(cls.INT, x, location)

    @classmethod
    def Sym(cls, s, location=None):
        """Construct a symbol token."""
        return cls(cls.SYMBOL, s, location)

    def __eq__(self, other):
        if isinstance(other, Token):
            return self.type == other.type and self.value == other.value
        else:
            # Convenience for comparing Tokens to strings and integers.
            return self.value == other

    def __repr__(self):
        return "Token({0.type!r}, {0.value!r}, loc={0.location!r})".format(self)


class Messages:
    """A class to represent a list of warning and error messages."""

    def __init__(self, msg=None, loc=None, *, warning=False):
        self.errors = []
        self.warnings = []
        if msg is not None:
            if warning:
                self.warnings.append((msg, loc))
            else:
                self.errors.append((msg, loc))

    def extend(self, messages: "Messages") -> "Messages":
        """Extend self with the warnings and errors in the other Messages object."""
        self.errors.extend(messages.errors)
        self.warnings.extend(messages.warnings)
        return self

    def err(self, msg: str, loc=None) -> None:
        """Record an error."""
        self.errors.append((msg, loc))

    def warn(self, msg: str, loc=None) -> None:
        """Record a warning."""
        self.warnings.append((msg, loc))


class HERAError(Exception):
    pass


class Constant(int):
    pass


class Label(int):
    pass


class DataLabel(int):
    pass
