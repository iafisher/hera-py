"""Utilities for the HERA interpreter.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import sys

from .data import HERAError, IntToken, Location, Messages, Token


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


def is_symbol(s):
    return isinstance(s, Token) and s.type == "SYMBOL"


def print_register_debug(target, v, *, to_stderr=True):
    file_ = sys.stderr if to_stderr else sys.stdout

    print("{0} = 0x{1:0>4x} = {1}".format(target, v), end="", file=file_)
    if v & 0x800:
        print(" = {}".format(from_u16(v)), end="", file=file_)
    if v < 128 and chr(v).isprintable():
        print(" = {!r}".format(chr(v)), end="", file=file_)
    print(file=file_)


REGISTER_BRANCHES = set(
    # Two concatenated lists so that the code formatter doesn't make this into 15 lines.
    ["BR", "BL", "BGE", "BLE", "BG", "BULE", "BUG", "BZ", "BNZ", "BC", "BNC", "BS"]
    + ["BNS", "BV", "BNV"]
)
RELATIVE_BRANCHES = set(b + "R" for b in REGISTER_BRANCHES)
BRANCHES = REGISTER_BRANCHES | RELATIVE_BRANCHES
DATA_STATEMENTS = set(
    ["CONSTANT", "DLABEL", "INTEGER", "LP_STRING", "TIGER_STRING", "DSKIP"]
)
BINARY_OPS = set(["ADD", "SUB", "MUL", "AND", "OR", "XOR"])
UNARY_OPS = set(["LSL", "LSR", "LSL8", "LSR8", "ASL", "ASR"])
ALSU_OPS = BINARY_OPS | UNARY_OPS


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
                caret = align_caret(loc.file_lines[loc.line - 1], loc.column) + "^"
                msg += ", line {} col {} of {}\n\n  {}\n  {}\n".format(
                    loc.line, loc.column, loc.path, loc.file_lines[loc.line - 1], caret
                )
            else:
                msg += ", line {} of {}\n\n  {}\n".format(
                    loc.line, loc.path, loc.file_lines[loc.line - 1]
                )

    sys.stderr.write(msg + "\n")


def align_caret(line, col):
    """Return the whitespace necessary to align a caret to underline the desired
    column in the line of text. Mainly this means handling tabs.
    """
    return "".join("\t" if c == "\t" else " " for c in line[: col - 1])


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


def handle_messages(state, ret_messages_pair):
    if (
        isinstance(ret_messages_pair, tuple)
        and len(ret_messages_pair) == 2
        and isinstance(ret_messages_pair[1], Messages)
    ):
        ret, messages = ret_messages_pair
    else:
        ret = None
        messages = ret_messages_pair

    for msg, loc in messages.warnings:
        if state.color:
            msg = ANSI_MAGENTA_BOLD + "Warning" + ANSI_RESET + ": " + msg
        else:
            msg = "Warning: " + msg
        print_message_with_location(msg, loc=loc)

    state.warning_count += len(messages.warnings)
    messages.warnings.clear()

    for msg, loc in messages.errors:
        if state.color:
            msg = ANSI_RED_BOLD + "Error" + ANSI_RESET + ": " + msg
        else:
            msg = "Error: " + msg
        print_message_with_location(msg, loc=loc)

    if messages.errors:
        sys.exit(3)
    else:
        return ret


# ANSI color codes (https://stackoverflow.com/questions/4842424/)
# When the --no-color flag is specified, these constants are set to the empty string, so
# you can use them unconditionally in your code without worrying about --no-color.


def make_ansi(*params):
    return "\033[" + ";".join(map(str, params)) + "m"


ANSI_RED_BOLD = make_ansi(31, 1)
ANSI_MAGENTA_BOLD = make_ansi(35, 1)
ANSI_RESET = make_ansi(0)
