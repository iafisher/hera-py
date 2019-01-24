"""Type-check HERA programs.

`typecheck` is the public interface of this module.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from contextlib import suppress
from typing import Dict, List

from . import config
from .data import Op, Token
from .utils import (
    BINARY_OPS,
    DATA_STATEMENTS,
    emit_error,
    is_register,
    is_symbol,
    print_warning,
    register_to_index,
    REGISTER_BRANCHES,
    RELATIVE_BRANCHES,
    UNARY_OPS,
)


def typecheck(program: List[Op]) -> Dict[str, int]:
    """Type-check the program and emit error messages as appropriate. Return the
    program's symbol table.
    """
    check_symbol_redeclaration(program)

    seen_code = False
    symbol_table = get_labels(program)
    for op in program:
        typecheck_op(op, symbol_table)

        if op.name in DATA_STATEMENTS:
            if seen_code:
                emit_error("data statement after code", loc=op.name)
        else:
            seen_code = True

        # Add constants to the symbol table as they are encountered, so that a given
        # constant is not in scope until after its declaration.
        if looks_like_a_CONSTANT(op):
            if out_of_range(op.args[1]):
                symbol_table[op.args[0]] = Constant(0)
            else:
                symbol_table[op.args[0]] = Constant(op.args[1])

    return symbol_table


def check_symbol_redeclaration(program: List[Op]):
    """Check if any symbols are redeclared in the program and emit error messages as
    appropriate.
    """
    symbols = set()
    for op in program:
        if op.name in ("CONSTANT", "LABEL", "DLABEL") and len(op.args) >= 1:
            symbol = op.args[0]
            if symbol in symbols:
                emit_error(
                    "symbol `{}` has already been defined".format(symbol), loc=op.name
                )
            else:
                symbols.add(symbol)


def get_labels(program: List[Op]) -> Dict[str, int]:
    """Return a dictionary mapping the labels and data labels (but not the constants) of
    the program to their concrete values.
    """
    symbol_table = {}
    # We need to maintain a separate dictionary of constants because DSKIP can take a
    # constant as its argument, which has to be resolved to set the data counter
    # correctly.
    constants = {}
    pc = 0
    dc = config.HERA_DATA_START
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
                with suppress(ValueError):
                    constants[op.args[0]] = Constant(op.args[1])
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

        # TODO: Can I move this elsewhere?
        if out_of_range(dc) and not out_of_range(odc):
            emit_error("past the end of available memory", loc=op.name)

    return symbol_table


def typecheck_op(op: Op, symbol_table: Dict[str, int]) -> bool:
    """Type-check a single HERA operation and emit error messages as appropriate."""
    n = len(op.args)
    nerrors = len(config.ERRORS)
    if op.name in ("SETLO", "SETHI"):
        assert_number_of_arguments(op, 2)
        n > 0 and assert_is_register(op.args[0])
        n > 1 and assert_is_integer(op.args[1], symbol_table, bits=8, signed=True)
    elif op.name in ("INC", "DEC"):
        assert_number_of_arguments(op, 2)
        n > 0 and assert_is_register(op.args[0])
        n > 1 and assert_in_range(op.args[1], symbol_table, lo=1, hi=65)
    elif op.name in BINARY_OPS:
        assert_number_of_arguments(op, 3)
        n > 0 and assert_is_register(op.args[0])
        n > 1 and assert_is_register(op.args[1])
        n > 2 and assert_is_register(op.args[2])
    elif op.name in UNARY_OPS or op.name in ("MOVE", "CMP", "NEG", "NOT"):
        assert_number_of_arguments(op, 2)
        n > 0 and assert_is_register(op.args[0])
        n > 1 and assert_is_register(op.args[1])
        if op.name == "NOT" and n == 2 and is_register(op.args[1]):
            with suppress(ValueError):
                i = register_to_index(op.args[1])
                if i == 11:
                    print_warning("don't use R11 with NOT", loc=op.args[1])
    elif op.name in ("SAVEF", "RSTRF", "FLAGS", "print_reg"):
        assert_number_of_arguments(op, 1)
        n > 0 and assert_is_register(op.args[0])
    elif op.name in ("FON", "FOFF", "FSET5"):
        assert_number_of_arguments(op, 1)
        n > 0 and assert_is_integer(op.args[0], symbol_table, bits=5, signed=False)
    elif op.name in ("FSET4", "SWI"):
        assert_number_of_arguments(op, 1)
        n > 0 and assert_is_integer(op.args[0], symbol_table, bits=4, signed=False)
    elif op.name in ("LOAD", "STORE"):
        assert_number_of_arguments(op, 3)
        n > 0 and assert_is_register(op.args[0])
        n > 1 and assert_is_integer(op.args[1], symbol_table, bits=5, signed=False)
        n > 2 and assert_is_register(op.args[2])
    elif op.name in ("CALL", "RETURN"):
        assert_number_of_arguments(op, 2)
        n > 0 and assert_is_register(op.args[0])
        n > 1 and assert_is_register_or_label(op.args[1], symbol_table)
        # Warn if first argument to CALL or RETURN isn't R12.
        if n >= 1 and is_register(op.args[0]):
            with suppress(ValueError):
                i = register_to_index(op.args[0])
                if i != 12:
                    msg = "first argument to {} should be R12".format(op.name)
                    print_warning(msg, loc=op.args[0])
        # Warn if second argument to RETURN isn't R13.
        if op.name == "RETURN" and n >= 2 and is_register(op.args[1]):
            with suppress(ValueError):
                i = register_to_index(op.args[1])
                if i != 13:
                    print_warning(
                        "second argument to RETURN should be R13", loc=op.args[1]
                    )
    elif op.name in REGISTER_BRANCHES:
        assert_number_of_arguments(op, 1)
        n > 0 and assert_is_register_or_label(op.args[0], symbol_table)
    elif op.name in RELATIVE_BRANCHES:
        assert_number_of_arguments(op, 1)
        if n > 0:
            if is_symbol(op.args[0]):
                assert_is_label(op.args[0])
            else:
                assert_is_integer(op.args[0], symbol_table, bits=8, signed=True)
    elif op.name in ("RTI", "CBON", "CON", "COFF", "CCBOFF", "NOP", "HALT"):
        assert_number_of_arguments(op, 0)
    elif op.name == "SET":
        assert_number_of_arguments(op, 2)
        n > 0 and assert_is_register(op.args[0])
        n > 1 and assert_is_integer(
            op.args[1], symbol_table, bits=16, signed=True, labels=True
        )
    elif op.name == "SETRF":
        assert_number_of_arguments(op, 2)
        n > 0 and assert_is_register(op.args[0])
        n > 1 and assert_is_integer(op.args[1], symbol_table, bits=16, signed=True)
    elif op.name in ("LABEL", "DLABEL"):
        assert_number_of_arguments(op, 1)
        n > 0 and assert_is_label(op.args[0])
    elif op.name == "CONSTANT":
        assert_number_of_arguments(op, 2)
        n > 0 and assert_is_label(op.args[0])
        n > 1 and assert_is_integer(op.args[1], symbol_table, bits=16, signed=True)
    elif op.name == "INTEGER":
        assert_number_of_arguments(op, 1)
        n > 0 and assert_is_integer(op.args[0], symbol_table, bits=16, signed=True)
    elif op.name in ("LP_STRING", "TIGER_STRING", "print", "println"):
        assert_number_of_arguments(op, 1)
        n > 0 and assert_is_string(op.args[0])
    elif op.name == "DSKIP":
        assert_number_of_arguments(op, 1)
        n > 0 and assert_is_integer(op.args[0], symbol_table, bits=16, signed=False)
    else:
        emit_error("unknown instruction `{}`".format(op.name), loc=op.name)
    return len(config.ERRORS) == nerrors


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
    if op.name in REGISTER_BRANCHES:
        if len(op.args) == 1 and is_register(op.args[0]):
            return 1
        else:
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
