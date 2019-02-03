from contextlib import suppress
from typing import Dict, List, Optional, Tuple

from .data import (
    Constant,
    DataLabel,
    Label,
    Op,
    Messages,
    Program,
    RegisterToken,
    Settings,
    Token,
    TOKEN,
)
from .op import (
    DataOperation,
    DebuggingOperation,
    Operation,
    RegisterBranch,
    RelativeBranch,
    resolve_ops,
)
from .utils import is_symbol


def check(oplist: List[Op], settings: Settings) -> Tuple[Optional[Program], Messages]:
    oplist, messages = resolve_ops(oplist)
    symbol_table, typecheck_messages = typecheck(oplist, settings=settings)
    messages.extend(typecheck_messages)
    if messages.errors:
        return (None, messages)

    oplist, preprocess_messages = convert_ops(oplist, symbol_table)
    messages.extend(preprocess_messages)

    data = []
    code = []
    for op in oplist:
        if isinstance(op, DataOperation):
            data.append(op)
        else:
            code.append(op)

    return (Program(data, code, symbol_table), messages)


def typecheck(
    program: List[Operation], settings=Settings()
) -> Tuple[Dict[str, int], Messages]:
    """Type-check the program and emit error messages as appropriate. Return the
    program's symbol table.
    """
    messages = check_symbol_redeclaration(program)

    seen_code = False
    symbol_table, label_messages = get_labels(program, settings)
    messages.extend(label_messages)

    for op in program:
        op_messages = op.typecheck(symbol_table)
        messages.extend(op_messages)

        if isinstance(op, DataOperation):
            if seen_code:
                messages.err("data statement after code", loc=op.loc)
        else:
            seen_code = True

        if settings.no_debug and isinstance(op, DebuggingOperation):
            messages.err(
                "debugging instructions disallowed with --no-debug flag", loc=op.loc
            )

        # Add constants to the symbol table as they are encountered, so that a given
        # constant is not in scope until after its declaration.
        if looks_like_a_CONSTANT(op):
            if out_of_range(op.args[1]):
                symbol_table[op.args[0]] = Constant(0)
            else:
                symbol_table[op.args[0]] = Constant(op.args[1])

    return (symbol_table, messages)


def check_symbol_redeclaration(program: List[Operation]) -> Messages:
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


def get_labels(
    program: List[Operation], settings: Settings
) -> Tuple[Dict[str, int], Messages]:
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
    dc = settings.data_start
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
    if isinstance(op, RegisterBranch):
        if len(op.args) == 1 and is_symbol(op.args[0]):
            return 3
        else:
            return 1
    elif op.name == "SET":
        return 2
    elif op.name == "CMP":
        return 2
    elif op.name == "SETRF":
        return 4
    elif op.name == "FLAGS":
        return 2
    elif op.name == "CALL":
        if len(op.args) == 2 and not isinstance(op.args[1], RegisterToken):
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


def convert_ops(
    oplist: List[Operation], symbol_table: Dict[str, int]
) -> Tuple[List[Operation], Messages]:
    """Convert the operations from pseudo-ops to real ops, and substitute values for
    labels and constants.

    The program must be type-checked before being passed to this function.
    """
    messages = Messages()
    retlist = []
    pc = 0
    for op in oplist:
        if isinstance(op, RelativeBranch) and is_symbol(op.args[0]):
            target = symbol_table[op.args[0]]
            jump = target - pc
            # TODO: Will this work? I think pc takes data statements into account here
            # erroneously.
            if jump < -128 or jump >= 128:
                messages.err("label is too far for a relative branch", loc=op.args[0])
            else:
                op.args[0] = jump
        else:
            op = substitute_label(op, symbol_table)

        new_ops = op.convert()
        for new_op in new_ops:
            new_op.loc = op.loc
            new_op.original = op
            retlist.append(new_op)

        if not isinstance(op, DataOperation):
            pc += len(new_ops)
    return (retlist, messages)


def substitute_label(op: Operation, symbol_table: Dict[str, int]) -> Operation:
    """Substitute any label in the instruction with its concrete value."""
    for i, arg in enumerate(op.args):
        if isinstance(arg, Token) and arg.type == TOKEN.SYMBOL:
            op.args[i] = symbol_table[arg]
    return op
