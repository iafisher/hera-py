"""Utilities for the HERA interpreter.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
import os.path
import sys

from . import config
from .data import HERAError, IntToken, Location, Token


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


def print_register_debug(target, v, *, to_stderr=True):
    file_ = sys.stderr if to_stderr else sys.stdout

    print("{0} = 0x{1:0>4x} = {1}".format(target, v), end="", file=file_)
    if v & 0x800:
        print(" = {}".format(from_u16(v)), end="", file=file_)
    if v < 128 and chr(v).isprintable():
        print(" = {!r}".format(chr(v)), end="", file=file_)
    print(file=file_)


def is_symbol(s):
    return isinstance(s, Token) and s.type == "SYMBOL"


REGISTER_BRANCHES = set(
    # Two concatenated lists so that the code formatter doesn't make this into 15 lines.
    ["BR", "BL", "BGE", "BLE", "BG", "BULE", "BUG", "BZ", "BNZ", "BC", "BNC", "BS"]
    + ["BNS", "BV", "BNV"]
)
RELATIVE_BRANCHES = set(b + "R" for b in REGISTER_BRANCHES)
BRANCHES = REGISTER_BRANCHES | RELATIVE_BRANCHES
DATA_STATEMENTS = set(["CONSTANT", "DLABEL", "INTEGER", "LP_STRING", "DSKIP"])
BINARY_OPS = set(["ADD", "SUB", "MUL", "AND", "OR", "XOR"])
UNARY_OPS = set(["LSL", "LSR", "LSL8", "LSR8", "ASL", "ASR"])
ALSU_OPS = BINARY_OPS | UNARY_OPS


def emit_error(msg, *, loc=None):
    """Register an error, to be printed at a later time.

    `loc` is either a Location or a Token object. If provided, the location and line of
    code will be indicated in the error message.
    """
    config.ERRORS.append((msg, loc))


def print_warning(msg, *, loc=None):
    """Print a warning message to stderr.

    `loc` is either a Location or a Token object. If provided, the location and line of
    code is indicated in the warning message.
    """
    msg = config.ANSI_MAGENTA_BOLD + "Warning" + config.ANSI_RESET + ": " + msg
    config.WARNING_COUNT += 1
    print_message_with_location(msg, loc=loc)


def print_message_with_location(msg, *, loc=None):
    """Print a message to stderr. If `loc` is provided as either a Location object, or
    a Token object with a `location` field, then the line of code that the location
    indicates will be printed with the message.
    """
    if isinstance(loc, (Token, IntToken)):
        loc = loc.location

    if isinstance(loc, Location):
        if loc.path == "-":
            loc = loc._replace(path="<stdin>")

        if loc.line is not None:
            if loc.column is not None:
                caret = _align_caret(loc.file_lines[loc.line - 1], loc.column) + "^"
                msg += ", line {} col {} of {}\n\n  {}\n  {}\n".format(
                    loc.line, loc.column, loc.path, loc.file_lines[loc.line - 1], caret
                )
            else:
                msg += ", line {} of {}\n\n  {}\n".format(
                    loc.line, loc.path, loc.file_lines[loc.line - 1]
                )

    sys.stderr.write(msg + "\n")


def _align_caret(line, col):
    """Return the whitespace necessary to align a caret to underline the desired
    column in the line of text. Mainly this means handling tabs.
    """
    return "".join("\t" if c == "\t" else " " for c in line[: col - 1])


def get_canonical_path(fpath):
    if fpath == "-" or fpath == "<string>":
        return fpath
    else:
        return os.path.realpath(fpath)


def op_to_string(op):
    """Convert a single operation to a string."""
    return "{}({})".format(op.name, ", ".join(str(a) for a in op.args))


def read_file(path) -> str:
    """Read a file and return its contents."""
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        raise HERAError('file "{}" does not exist'.format(path))
    except PermissionError:
        raise HERAError('permission denied to open file "{}"'.format(path))
    except OSError:
        raise HERAError('could not open file "{}"'.format(path))


def pad(s, n):
    return (" " * (n - len(s))) + s
