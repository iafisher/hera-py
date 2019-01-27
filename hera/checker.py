from contextlib import suppress
from typing import Dict, List, Tuple

from .data import Constant, DataLabel, Label, Op, Messages, Program, State, Token
from .op import resolve_ops
from .utils import (
    DATA_STATEMENTS,
    is_register,
    is_symbol,
    REGISTER_BRANCHES,
    RELATIVE_BRANCHES,
)


def check(oplist: List[Op], state: State) -> Tuple[Program, Messages]:
    oplist, messages = resolve_ops(oplist)
    symbol_table, typecheck_messages = typecheck(oplist, state=state)
    messages.extend(typecheck_messages)
    if messages.errors:
        return (oplist, messages)

    oplist, preprocess_messages = preprocess(oplist, symbol_table, state=state)
    messages.extend(preprocess_messages)

    data = []
    code = []
    for op in oplist:
        if op.name in DATA_STATEMENTS:
            data.append(op)
        else:
            code.append(op)

    return (Program(data, code, symbol_table), messages)


def typecheck(program: List[Op], state=State()) -> Tuple[Dict[str, int], Messages]:
    """Type-check the program and emit error messages as appropriate. Return the
    program's symbol table.
    """
    messages = check_symbol_redeclaration(program, state)

    seen_code = False
    symbol_table, label_messages = get_labels(program, state)
    messages.extend(label_messages)

    for op in program:
        op_messages = op.typecheck(symbol_table)
        messages.extend(op_messages)

        if op.name in DATA_STATEMENTS:
            if seen_code:
                messages.err("data statement after code", loc=op.loc)
        else:
            seen_code = True

        # Add constants to the symbol table as they are encountered, so that a given
        # constant is not in scope until after its declaration.
        if looks_like_a_CONSTANT(op):
            if out_of_range(op.args[1]):
                symbol_table[op.args[0]] = Constant(0)
            else:
                symbol_table[op.args[0]] = Constant(op.args[1])

    return (symbol_table, messages)


def check_symbol_redeclaration(program: List[Op], state: State) -> Messages:
    """Check if any symbols are redeclared in the program and return the error
    messages.
    """
    messages = Messages()
    symbols = set()
    for op in program:
        if op.name in ("CONSTANT", "LABEL", "DLABEL") and len(op.args) >= 1:
            symbol = op.args[0]
            if symbol in symbols:
                messages.err(
                    "symbol `{}` has already been defined".format(symbol), loc=op.loc
                )
            else:
                symbols.add(symbol)
    return messages


def get_labels(program: List[Op], state: State) -> Tuple[Dict[str, int], Messages]:
    """Return a dictionary mapping the labels and data labels (but not the constants) of
    the program to their concrete values.
    """
    messages = Messages()
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
            messages.err("past the end of available memory", loc=op.loc)

    return (symbol_table, messages)


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
) -> Tuple[List[Op], Messages]:
    """Preprocess the program into valid input for the exec_many method on the
    VirtualMachine class.

    This function does the following
        - Replaces pseudo-instructions with real ones.
        - Resolves labels into their line numbers.

    The program must be type-checked before being passed to this function.
    """
    messages = Messages()
    nprogram = []
    for op in program:
        if op.name in RELATIVE_BRANCHES and is_symbol(op.args[0]):
            pc = len(nprogram)
            target = symbol_table[op.args[0]]
            jump = target - pc
            if jump < -128 or jump >= 128:
                messages.err("label is too far for a relative branch", loc=op.args[0])
            else:
                op.args[0] = jump
        else:
            op = substitute_label(op, symbol_table)

        for new_op in op.convert():
            new_op.loc = op.loc
            new_op.original = op
            nprogram.append(new_op)
    return (nprogram, messages)


def substitute_label(op: Op, symbol_table: Dict[str, int]) -> Op:
    """Substitute any label in the instruction with its concrete value."""
    for i, arg in enumerate(op.args):
        if isinstance(arg, Token) and arg.type == "SYMBOL":
            op.args[i] = symbol_table[arg]
    return op
