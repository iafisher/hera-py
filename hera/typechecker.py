"""Type-check HERA programs.

`typecheck` is the public interface of this module.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from typing import Dict, List, Optional, Tuple

from .config import HERA_DATA_START
from .data import Op, Token
from .utils import (
    BINARY_OPS,
    emit_error,
    is_symbol,
    register_to_index,
    REGISTER_BRANCHES,
    RELATIVE_BRANCHES,
    UNARY_OPS,
)


def typecheck(program: List[Op]) -> Optional[Dict[str, int]]:
    """Type-check the program and emit error messages as appropriate. Return the
    program's symbol table if the program is well-typed, return None otherwise.
    """
    errors = check_symbol_redeclaration(program)

    symbol_table, symbol_table_errors = get_labels(program)
    errors = errors or symbol_table_errors
    for op in program:
        if not typecheck_op(op, symbol_table):
            errors = True

        if looks_like_a_CONSTANT(op):
            if out_of_range(op.args[1]):
                symbol_table[op.args[0]] = Constant(0)
            else:
                symbol_table[op.args[0]] = Constant(op.args[1])

    return symbol_table if not errors else None


def check_symbol_redeclaration(program: List[Op]) -> bool:
    """Check if any symbols are redeclared in the program and emit error messages as
    appropriate. Return True if any redeclaration occurred.
    """
    errors = False
    symbols = set()
    for op in program:
        if op.name in ("CONSTANT", "LABEL", "DLABEL") and len(op.args) >= 1:
            symbol = op.args[0]
            if symbol in symbols:
                errors = True
                emit_error(
                    "symbol `{}` has already been defined".format(symbol), loc=op.name
                )
            else:
                symbols.add(symbol)
    return errors


def get_labels(program: List[Op]) -> Tuple[Dict[str, int], bool]:
    """Return a dictionary mapping the labels and data labels (but not the constants) of
    the program to their concrete values.

    Return value is (symbol_table, errors).
    """
    errors = False
    symbol_table = {}
    # We need to maintain a separate dictionary of constants because DSKIP can take a
    # constant as its argument, which has to be resolved to set the data counter
    # correctly.
    constants = {}
    pc = 0
    dc = HERA_DATA_START
    for op in program:
        odc = dc
        if op.name == "LABEL":
            if len(op.args) == 1:
                symbol_table[op.args[0]] = Label(pc)
        elif op.name == "DLABEL":
            if len(op.args) == 1:
                if out_of_range(dc):
                    # If data counter has overflowed, put in a dummy value to avoid
                    # further overflow error messages.
                    symbol_table[op.args[0]] = DataLabel(0)
                else:
                    symbol_table[op.args[0]] = DataLabel(dc)
        elif op.name == "CONSTANT":
            if len(op.args) == 2:
                try:
                    c = Constant(op.args[1])
                except ValueError:
                    continue
                else:
                    constants[op.args[0]] = c
        elif op.name == "INTEGER":
            dc += 1
        elif op.name == "LP_STRING":
            if len(op.args) == 1 and isinstance(op.args[0], str):
                dc += len(op.args[0]) + 1
        elif op.name == "DSKIP":
            if len(op.args) == 1:
                if isinstance(op.args[0], int):
                    dc += op.args[0]
                elif op.args[0] in constants:
                    dc += constants[op.args[0]]
        else:
            pc += operation_length(op)

        if out_of_range(dc) and not out_of_range(odc):
            emit_error("past the end of available memory", loc=op.name)
            errors = True

    return symbol_table, errors


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


def operation_length(op):
    # TODO: Better name.
    if op.name in REGISTER_BRANCHES:
        return 3
    elif op.name == "SET":
        return 2
    elif op.name == "CMP":
        return 2
    elif op.name == "SETRF":
        return 4
    elif op.name == "FLAGS":
        return 2
    elif op.name == "CALL":
        if len(op.args) == 2 and isinstance(op.args[1], int) or is_symbol(op.args[1]):
            return 3
        else:
            return 1
    elif op.name == "NEG":
        return 2
    elif op.name == "NOT":
        return 3
    else:
        return 1


def looks_like_a_CONSTANT(op):
    return (
        op.name == "CONSTANT"
        and len(op.args) == 2
        and isinstance(op.args[0], str)
        and isinstance(op.args[1], int)
    )


def out_of_range(n):
    return n < -32768 or n >= 65536


class Constant(int):
    pass


class Label(int):
    pass


class DataLabel(int):
    pass
