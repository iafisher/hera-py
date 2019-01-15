"""Type-check HERA programs.

`typecheck` is the public interface of this module.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from typing import Dict, List

from .data import Op, Token
from .symtab import Constant, DataLabel
from .utils import (
    BINARY_OPS,
    emit_error,
    is_symbol,
    register_to_index,
    REGISTER_BRANCHES,
    RELATIVE_BRANCHES,
    UNARY_OPS,
)


def typecheck(program: List[Op], symbol_table: Dict[str, int]) -> True:
    """Type-check the program and emit errors as appropriate. Return True if the
    program is well-typed.
    """
    error_free = True
    for op in program:
        if not typecheck_op(op, symbol_table):
            error_free = False
    return error_free


def typecheck_op(op: Op, symbol_table: Dict[str, int]) -> bool:
    """Type-check a single HERA operation and emit error messages as appropriate. Return
    True if no errors were detected.
    """
    n = len(op.args)
    if op.name in ("SETLO", "SETHI"):
        e = assert_number_of_arguments(op, 2)
        e1 = n > 0 and assert_is_register(op.args[0])
        e2 = n > 1 and assert_is_integer(op.args[1], symbol_table, bits=8, signed=True)
        return e and e1 and e2
    elif op.name in ("INC", "DEC"):
        e = assert_number_of_arguments(op, 2)
        e1 = n > 0 and assert_is_register(op.args[0])
        e2 = n > 1 and assert_in_range(op.args[1], symbol_table, lo=1, hi=65)
        return e and e1 and e2
    elif op.name in BINARY_OPS:
        e = assert_number_of_arguments(op, 3)
        e1 = n > 0 and assert_is_register(op.args[0])
        e2 = n > 1 and assert_is_register(op.args[1])
        e3 = n > 2 and assert_is_register(op.args[2])
        return e and e1 and e2 and e3
    elif op.name in UNARY_OPS or op.name in ("MOVE", "CMP", "NEG", "NOT"):
        e = assert_number_of_arguments(op, 2)
        e1 = n > 0 and assert_is_register(op.args[0])
        e2 = n > 1 and assert_is_register(op.args[1])
        return e and e1 and e2
    elif op.name in ("SAVEF", "RSTRF", "FLAGS", "print_reg"):
        e = assert_number_of_arguments(op, 1)
        e1 = n > 0 and assert_is_register(op.args[0])
        return e and e1
    elif op.name in ("FON", "FOFF", "FSET5"):
        e = assert_number_of_arguments(op, 1)
        e1 = n > 0 and assert_is_integer(op.args[0], symbol_table, bits=5, signed=False)
        return e and e1
    elif op.name in ("FSET4", "SWI"):
        e = assert_number_of_arguments(op, 1)
        e1 = n > 0 and assert_is_integer(op.args[0], symbol_table, bits=4, signed=False)
        return e and e1
    elif op.name in ("LOAD", "STORE"):
        e = assert_number_of_arguments(op, 3)
        e1 = n > 0 and assert_is_register(op.args[0])
        e2 = n > 1 and assert_is_integer(op.args[1], symbol_table, bits=5, signed=False)
        e3 = n > 2 and assert_is_register(op.args[2])
        return e and e1 and e2 and e3
    elif op.name in ("CALL", "RETURN"):
        e = assert_number_of_arguments(op, 2)
        e1 = n > 0 and assert_is_register(op.args[0])
        e2 = n > 1 and assert_is_register_or_label(op.args[1], symbol_table)
        return e and e1 and e2
    elif op.name in REGISTER_BRANCHES:
        e = assert_number_of_arguments(op, 1)
        e1 = n > 0 and assert_is_register_or_label(op.args[0], symbol_table)
        return e and e1
    elif op.name in RELATIVE_BRANCHES:
        e = assert_number_of_arguments(op, 1)
        if n > 0:
            if is_symbol(op.args[0]):
                msg = "relative branches cannot use labels"
                msg += " (why not use {} instead?)".format(op.name[:-1])
                emit_error(msg, loc=op.args[0])
                e1 = False
            else:
                e1 = assert_is_integer(op.args[0], symbol_table, bits=8, signed=True)
        return e and e1
    elif op.name in ("RTI", "CBON", "CON", "COFF", "CCBOFF", "NOP", "HALT"):
        return assert_number_of_arguments(op, 0)
    elif op.name == "SET":
        e = assert_number_of_arguments(op, 2)
        e1 = n > 0 and assert_is_register(op.args[0])
        e2 = n > 1 and assert_is_integer(
            op.args[1], symbol_table, bits=16, signed=True, labels=True
        )
        return e and e1 and e2
    elif op.name == "SETRF":
        e = assert_number_of_arguments(op, 2)
        e1 = n > 0 and assert_is_register(op.args[0])
        e2 = n > 1 and assert_is_integer(op.args[1], symbol_table, bits=16, signed=True)
        return e and e1 and e2
    elif op.name in ("LABEL", "DLABEL"):
        e = assert_number_of_arguments(op, 1)
        e1 = n > 0 and assert_is_label(op.args[0])
        return e and e1
    elif op.name == "CONSTANT":
        e = assert_number_of_arguments(op, 2)
        e1 = n > 0 and assert_is_label(op.args[0])
        e2 = n > 1 and assert_is_integer(op.args[1], symbol_table, bits=16, signed=True)
        return e and e1 and e2
    elif op.name == "INTEGER":
        e = assert_number_of_arguments(op, 1)
        e1 = n > 0 and assert_is_integer(op.args[0], symbol_table, bits=16, signed=True)
        return e and e1
    elif op.name in ("LP_STRING", "print", "println"):
        e = assert_number_of_arguments(op, 1)
        e1 = n > 0 and assert_is_string(op.args[0])
        return e and e1
    elif op.name == "DSKIP":
        e = assert_number_of_arguments(op, 1)
        e1 = n > 0 and assert_is_integer(
            op.args[0], symbol_table, bits=16, signed=False
        )
        return e and e1
    else:
        emit_error("unknown instruction `{}`".format(op.name), loc=op.name)
        return False


def assert_number_of_arguments(op, nargs):
    if len(op.args) < nargs:
        emit_error(
            "too few args to {} (expected {})".format(op.name, nargs), loc=op.name
        )
        return False
    elif nargs < len(op.args):
        emit_error(
            "too many args to {} (expected {})".format(op.name, nargs), loc=op.name
        )
        return False
    else:
        return True


def assert_is_register(arg):
    if not isinstance(arg, Token) or arg.type != "REGISTER":
        emit_error("expected register", loc=arg)
        return False

    if arg.lower() == "pc":
        emit_error("program counter cannot be accessed or changed directly", loc=arg)
        return False

    try:
        register_to_index(arg)
    except ValueError:
        emit_error("{} is not a valid register".format(arg), loc=arg)
        return False
    else:
        return True


def assert_is_register_or_label(arg, symbol_table):
    if not isinstance(arg, Token) or arg.type not in ("REGISTER", "SYMBOL"):
        emit_error("expected register or label", loc=arg)
        return False

    if arg.type == "REGISTER":
        return assert_is_register(arg)
    else:
        try:
            val = symbol_table[arg]
        except KeyError:
            emit_error("undefined symbol", loc=arg)
            return False
        else:
            if isinstance(val, Constant):
                emit_error("constant cannot be used as label", loc=arg)
                return False
            elif isinstance(val, DataLabel):
                emit_error("data label cannot be used as branch label", loc=arg)
                return False
            else:
                return True


def assert_is_label(arg):
    if not is_symbol(arg):
        emit_error("expected label", loc=arg)
        return False
    else:
        return True


def assert_is_string(arg):
    if not isinstance(arg, Token) or arg.type != "STRING":
        emit_error("expected string literal", loc=arg)
        return False
    else:
        return True


def assert_is_integer(arg, symbol_table, *, bits, signed, labels=False):
    if signed:
        lo = (-2) ** (bits - 1)
    else:
        lo = 0
    hi = 2 ** bits

    return assert_in_range(arg, symbol_table, lo=lo, hi=hi, labels=labels)


def assert_in_range(arg, symbol_table, *, lo, hi, labels=False):
    if is_symbol(arg):
        try:
            arg = symbol_table[arg]
        except KeyError:
            emit_error("undefined constant", loc=arg)
            return False
        else:
            if not labels and not isinstance(arg, Constant):
                emit_error("cannot use label as constant", loc=arg)
                return False

    if not isinstance(arg, int):
        emit_error("expected integer", loc=arg)
        return False

    if arg < lo or arg >= hi:
        emit_error("integer must be in range [{}, {})".format(lo, hi), loc=arg)
        return False
    else:
        return True
