"""Utilities for the HERA interpreter.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
import os.path
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


NAMED_REGISTERS = {"rt": 11, "fp": 14, "sp": 15, "pc_ret": 13, "fp_alt": 12, "pc": -1}


def register_to_index(rname):
    """Return the index of the register with the given name in the register array."""
    original = rname
    rname = rname.lower()
    if rname in NAMED_REGISTERS:
        return NAMED_REGISTERS[rname]
    elif rname.startswith("r"):
        v = int(rname[1:])
        if 0 <= v < 16:
            return v
    raise ValueError("{} is not a valid register".format(original))


def is_register(s):
    return (s[0] in "rR" and s[1:].isdigit()) or s.lower() in NAMED_REGISTERS


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


REGISTER_BRANCHES = set(
    # Two lists instead of one so that the code formatter doesn't make this into a
    # dozen lines.
    ["BR", "BL", "BGE", "BLE", "BG", "BULE", "BUG", "BZ", "BNZ", "BC", "BNC", "BS"]
    + ["BNS", "BV", "BNV"]
)
RELATIVE_BRANCHES = set(b + "R" for b in REGISTER_BRANCHES)
DATA_STATEMENTS = set(["CONSTANT", "DLABEL", "INTEGER", "LP_STRING", "DSKIP"])


def emit_error(msg, *, loc=None, line=None, column=None, exit=False):
    """Print an error message to stderr."""
    msg = config.ANSI_RED_BOLD + "Error" + config.ANSI_RESET + ": " + msg
    config.ERROR_COUNT += 1
    _emit_msg(msg, loc=loc, line=line, column=column, exit=exit)


def emit_warning(msg, *, loc=None, line=None, column=None):
    """Print a error warning to stderr."""
    msg = config.ANSI_MAGENTA_BOLD + "Warning" + config.ANSI_RESET + ": " + msg
    config.WARNING_COUNT += 1
    _emit_msg(msg, loc=loc, line=line, column=column, exit=False)


def _emit_msg(msg, *, loc=None, line=None, column=None, exit=False):
    if loc is not None and loc.path == "-":
        loc = loc._replace(path="<stdin>")

    if line is not None and loc is not None:
        if column is not None:
            caret = _align_caret(loc.lines[line - 1], column) + "^"
            msg += ", line {} col {} of {}\n\n  {}\n  {}\n".format(
                line, column, loc.path, loc.lines[line - 1], caret
            )
        else:
            msg += ", line {} of {}\n\n  {}\n".format(
                line, loc.path, loc.lines[line - 1]
            )
    sys.stderr.write(msg + "\n")
    if exit:
        sys.exit(3)


def _align_caret(line, col):
    """Return the whitespace necessary to align a caret to underline the desired
    column in the line of text. Mainly this means handling tabs.
    """
    return "".join("\t" if c == "\t" else " " for c in line[: col - 1])


def get_canonical_path(fpath):
    if fpath == "-":
        return fpath
    else:
        return os.path.realpath(fpath)
