from contextlib import suppress
from typing import Dict, List

from .data import Constant, DataLabel, Label, Op, Program, State, Token
from .op import resolve_ops
from .utils import (
    DATA_STATEMENTS,
    handle_errors,
    is_register,
    is_symbol,
    REGISTER_BRANCHES,
    RELATIVE_BRANCHES,
)


def check(program: List[Op], state: State) -> Program:
    program = resolve_ops(program, state=state)
    symbol_table = typecheck(program, state=state)
    handle_errors(state)

    program = preprocess(program, symbol_table, state=state)
    handle_errors(state)
    return program, symbol_table


def typecheck(program: List[Op], state=State()) -> Dict[str, int]:
    """Type-check the program and emit error messages as appropriate. Return the
    program's symbol table.
    """
    check_symbol_redeclaration(program, state)

    seen_code = False
    symbol_table = get_labels(program, state)
    for op in program:
        errors = op.typecheck(symbol_table)

        for is_error, msg, loc in errors:
            if is_error:
                state.error(msg, loc=loc)
            else:
                state.warning(msg, loc=loc)

        if op.name in DATA_STATEMENTS:
            if seen_code:
                state.error("data statement after code", loc=op.loc)
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


def check_symbol_redeclaration(program: List[Op], state: State):
    """Check if any symbols are redeclared in the program and emit error messages as
    appropriate.
    """
    symbols = set()
    for op in program:
        if op.name in ("CONSTANT", "LABEL", "DLABEL") and len(op.args) >= 1:
            symbol = op.args[0]
            if symbol in symbols:
                state.error(
                    "symbol `{}` has already been defined".format(symbol), loc=op.loc
                )
            else:
                symbols.add(symbol)


def get_labels(program: List[Op], state: State) -> Dict[str, int]:
    """Return a dictionary mapping the labels and data labels (but not the constants) of
    the program to their concrete values.
    """
    symbol_table = {}
    # We need to maintain a separate dictionary of constants because DSKIP can take a
    # constant as its argument, which has to be resolved to set the data counter
    # correctly.
    constants = {}
    pc = 0
    dc = state.data_start
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
        elif op.name == "LP_STRING" or op.name == "TIGER_STRING":
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
            state.error("past the end of available memory", loc=op.loc)

    return symbol_table


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
        if len(op.args) == 2 and (isinstance(op.args[1], int) or is_symbol(op.args[1])):
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


def preprocess(
    program: List[Op], symbol_table: Dict[str, int], state=State()
) -> List[Op]:
    """Preprocess the program into valid input for the exec_many method on the
    VirtualMachine class.

    This function does the following
        - Replaces pseudo-instructions with real ones.
        - Resolves labels into their line numbers.

    The program must be type-checked before being passed to this function.
    """
    nprogram = []
    for op in program:
        if op.name in RELATIVE_BRANCHES and is_symbol(op.args[0]):
            pc = len(nprogram)
            target = symbol_table[op.args[0]]
            jump = target - pc
            if jump < -128 or jump >= 128:
                state.error("label is too far for a relative branch", loc=op.args[0])
            else:
                op.args[0] = jump
        else:
            op = substitute_label(op, symbol_table)

        for new_op in op.convert():
            new_op.loc = op.loc
            new_op.original = op
            nprogram.append(new_op)
    return nprogram


def substitute_label(op: Op, symbol_table: Dict[str, int]) -> Op:
    """Substitute any label in the instruction with its concrete value."""
    for i, arg in enumerate(op.args):
        if isinstance(arg, Token) and arg.type == "SYMBOL":
            op.args[i] = symbol_table[arg]
    return op
