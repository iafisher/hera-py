"""Utilities for the HERA interpreter.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
import sys

from lark import Token

from . import config


class HERAError(Exception):
    def __init__(self, msg, line=None, column=None):
        super().__init__(msg)
        self.line = line
        self.column = column


def to_u16(n):
    """Reinterpret the signed integer `n` as a 16-bit unsigned integer.

    If `n` is too large for 16 bits, OverflowError is raised.
    """
    # Note that we allow positive values up to 2**16, but negative values only
    # down to -2**15.
    if n >= 2 ** 16 or n < -2 ** 15:
        raise OverflowError("signed integer too large for 16 bits")

    if n < 0:
        return 2 ** 16 + n
    else:
        return n


def from_u16(n):
    """Reinterpret the unsigned 16-bit integer `n` as a signed integer."""
    if n >= 2 ** 15:
        return -(2 ** 16 - n)
    else:
        return n


def to_u32(n):
    """Reinterpret the signed integer `n` as an unsigned 32-bit integer.

    If `n` is too large for 32 bits, OverflowError is raised.
    """
    # Note that we allow positive values up to 2**32, but negative values only
    # down to -2**31.
    if n >= 2 ** 32 or n < -2 ** 31:
        raise OverflowError("signed integer too large for 16 bits")

    if n < 0:
        return 2 ** 32 + n
    else:
        return n


def register_to_index(rname):
    """Return the index of the register with the given name in the register array."""
    original = rname
    rname = rname.lower()
    if rname == "rt":
        return 11
    elif rname.startswith("r"):
        v = int(rname[1:])
        if 0 <= v < 16:
            return v
    elif rname == "fp":
        return 14
    elif rname == "sp":
        return 15
    raise ValueError("{} is not a valid register".format(original))


class IntToken(int):
    def __new__(cls, value, line=None, column=None, **kwargs):
        self = super(IntToken, cls).__new__(cls, value, **kwargs)
        self.line = line
        self.column = column
        return self


def print_register_debug(target, v, *, to_stderr=True):
    file_ = sys.stderr if to_stderr else sys.stdout

    print("{0} = 0x{1:0>4x} = {1}".format(target, v), end="", file=file_)
    if v & 0x800:
        print(" = {}".format(from_u16(v)), end="", file=file_)
    if v < 128 and chr(v).isprintable():
        print(" = {!r}".format(chr(v)), end="", file=file_)
    print(file=file_)


def copy_token(val, otkn):
    """Convert the string `val` into a Token with the same line and column numbers as
    `otkn`.
    """
    if isinstance(otkn, Token):
        return Token(otkn.type, val, line=otkn.line, column=otkn.column)
    else:
        return val


def is_symbol(s):
    return isinstance(s, Token) and s.type == "SYMBOL"


def is_relative_branch(opname):
    return opname.startswith("B") and opname.endswith("R") and opname != "BR"


def emit_error(msg, *, line=None, column=None, exit=False):
    """Print an error message to stderr."""
    msg = config.ANSI_RED_BOLD + "Error" + config.ANSI_RESET + ": " + msg
    config.SEEN_ERROR = True
    _emit_msg(msg, line=line, column=column, exit=exit)


def emit_warning(msg, *, line=None, column=None):
    """Print a error warning to stderr."""
    msg = config.ANSI_MAGENTA_BOLD + "Warning" + config.ANSI_RESET + ": " + msg
    _emit_msg(msg, line=line, column=column, exit=False)


def _emit_msg(msg, *, line=None, column=None, exit=False):
    if line is not None and config.LINES is not None:
        if column is not None:
            caret = _align_caret(config.LINES[line - 1], column) + "^"
            msg += ", line {} col {}\n\n  {}\n  {}\n".format(
                line, column, config.LINES[line - 1], caret
            )
        else:
            msg += ", line {}\n\n  {}\n".format(line, config.LINES[line - 1])
    sys.stderr.write(msg + "\n")
    if exit:
        sys.exit(exit)


def _align_caret(line, col):
    """Return the whitespace necessary to align a caret to underline the desired
    column in the line of text. Mainly this means handling tabs.
    """
    return "".join("\t" if c == "\t" else " " for c in line[: col - 1])
