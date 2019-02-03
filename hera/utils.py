"""Utilities for the hera-py system.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import sys

from .data import HERAError, Location, Messages, Token


def to_u16(n):
    """Reinterpret the signed integer `n` as a 16-bit unsigned integer.

    If `n` is too large for 16 bits, a HERAError is raised.
    """
    # Note that we allow positive values up to 2**16, but negative values only
    # down to -2**15.
    if n >= 2 ** 16 or n < -2 ** 15:
        raise HERAError("signed integer too large for 16 bits")

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

    If `n` is too large for 32 bits, a HERAError is raised.
    """
    # Note that we allow positive values up to 2**32, but negative values only
    # down to -2**31.
    if n >= 2 ** 32 or n < -2 ** 31:
        raise HERAError("signed integer too large for 16 bits")

    if n < 0:
        return 2 ** 32 + n
    else:
        return n


NAMED_REGISTERS = {"rt": 11, "fp": 14, "sp": 15, "pc_ret": 13, "fp_alt": 12}


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
    raise HERAError("{} is not a valid register".format(original))


def format_int(v, *, spec="xdsc"):
    """Return a string of the form "... = ... = ..." where each ellipsis stands for a
    formatted integer determined by a character in the `spec` parameter. The following
    formats are supported: d for decimal, x for hexadecimal, o for octal, b for binary,
    c for character literal, and s for signed integer. The latter two formats only
    generate output when applicable, e.g. for integers that actually represent printable
    characters and signed integers, respectively. Output can be forced for either of
    these formats by capitalizing the letter.
    """
    ret = []
    for c in spec:
        if c == "d":
            ret.append(str(v))
        elif c == "x":
            ret.append("0x{:0>4x}".format(v))
        elif c == "o":
            ret.append("0o{:0>8o}".format(v))
        elif c == "b":
            ret.append("0b{:0>16b}".format(v))
        elif c == "c":
            if v < 128 and chr(v).isprintable():
                ret.append(repr(chr(v)))
        elif c == "C":
            if v < 128:
                ret.append(repr(chr(v)))
            else:
                ret.append("not an ASCII character")
        elif c == "s":
            if v & 0x8000:
                ret.append(str(from_u16(v)))
        elif c == "S":
            if v & 0x8000:
                ret.append(str(from_u16(v)))
            else:
                ret.append("not a signed integer")
        else:
            raise RuntimeError("unknown format specifier: " + c)
    return " = ".join(ret)


def print_warning(settings, msg, *, loc=None):
    if settings.color:
        msg = ANSI_MAGENTA_BOLD + "Warning" + ANSI_RESET + ": " + msg
    else:
        msg = "Warning: " + msg
    print_message(msg, loc=loc)


def print_error(settings, msg, *, loc=None):
    if settings.color:
        msg = ANSI_RED_BOLD + "Error" + ANSI_RESET + ": " + msg
    else:
        msg = "Error: " + msg
    print_message(msg, loc=loc)


def print_message(msg, *, loc=None):
    """Print a message to stderr. If `loc` is provided as either a Location object, or
    a Token object with a `location` field, then the line of code that the location
    indicates will be printed with the message.
    """
    if isinstance(loc, Token):
        loc = loc.location

    if isinstance(loc, Location):
        linetext = loc.file_lines[loc.line - 1]
        if linetext.strip():
            caret = align_caret(linetext, loc.column) + "^"
            msg += ", line {} col {} of {}\n\n  {}\n  {}\n".format(
                loc.line, loc.column, loc.path, linetext, caret
            )
        else:
            msg += ", line {0.line} col {0.column} of {0.path}".format(loc)

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


def handle_messages(settings, ret_messages_pair):
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
        print_warning(settings, msg, loc=loc)

    settings.warning_count += len(messages.warnings)
    messages.warnings.clear()

    for msg, loc in messages.errors:
        print_error(settings, msg, loc=loc)

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
