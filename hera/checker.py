"""Type-checking and pseudo-op conversion.

Note that the code for type-checking individual operations lives in hera/op.py. This
module contains the code for program-wide type-checking.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: Feburary 2019
"""
from contextlib import suppress
from typing import Dict, List, Optional, Set, Tuple  # noqa: F401

from .data import (
    Constant,
    DataLabel,
    DebugInfo,
    Label,
    Messages,
    Program,
    Settings,
    Token,
)
from .op import (
    DataOperation,
    DebuggingOperation,
    AbstractOperation,
    RegisterBranch,
    RelativeBranch,
    LABEL,
    RTI,
    SWI,
)


def check(
    oplist: List[AbstractOperation], settings: Settings
) -> Tuple[Program, Messages]:
    symbol_table, messages = typecheck(oplist, settings=settings)
    if messages.errors:
        return (Program([], [], {}, None), messages)

    debug_info = None  # type: Optional[DebugInfo]
    if settings.debug:
        labels = labels_to_line_numbers(oplist)
        debug_info = DebugInfo(labels)
    else:
        debug_info = None

    oplist, preprocess_messages = convert_ops(oplist, symbol_table)
    messages.extend(preprocess_messages)

    data = []
    code = []
    for op in oplist:
        if isinstance(op, DataOperation):
            data.append(op)
        else:
            code.append(op)

    return (Program(data, code, symbol_table, debug_info), messages)


def typecheck(
    program: List[AbstractOperation], settings=Settings()
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

        if not settings.allow_interrupts and isinstance(op, (RTI, SWI)):
            messages.err("hera-py does not support {}".format(op.name), loc=op.loc)

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


def check_symbol_redeclaration(program: List[AbstractOperation]) -> Messages:
    """Check if any symbols are redeclared in the program and return the error
    messages.
    """
    messages = Messages()
    symbols = set()  # type: Set[str]
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
    program: List[AbstractOperation], settings: Settings
) -> Tuple[Dict[str, int], Messages]:
    """Return a dictionary mapping the labels and data labels (but not the constants) of
    the program to their concrete values.
    """
    messages = Messages()
    symbol_table = {}  # type: Dict[str, int]
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


def operation_length(op: AbstractOperation) -> int:
    if isinstance(op, RegisterBranch):
        if len(op.tokens) == 1 and op.tokens[0].type == Token.SYMBOL:
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
        if len(op.tokens) == 2 and op.tokens[1].type != Token.REGISTER:
            return 3
        else:
            return 1
    elif op.name == "NEG":
        return 2
    elif op.name == "NOT":
        return 3
    else:
        return 1


def looks_like_a_CONSTANT(op: AbstractOperation) -> bool:
    return (
        op.name == "CONSTANT"
        and len(op.args) == 2
        and isinstance(op.args[0], str)
        and isinstance(op.args[1], int)
    )


def out_of_range(n: int) -> bool:
    return n < -32768 or n >= 65536


def convert_ops(
    oplist: List[AbstractOperation], symbol_table: Dict[str, int]
) -> Tuple[List[AbstractOperation], Messages]:
    """Convert the operations from pseudo-ops to real ops, and substitute values for
    labels and constants.

    The program must be type-checked before being passed to this function.
    """
    messages = Messages()
    retlist = []
    pc = 0
    for op in oplist:
        if isinstance(op, RelativeBranch) and op.tokens[0].type == Token.SYMBOL:
            target = symbol_table[op.args[0]]
            jump = target - pc
            # TODO: Will this work? I think pc takes data statements into account here
            # erroneously.
            if jump < -128 or jump >= 128:
                messages.err("label is too far for a relative branch", loc=op.tokens[0])
            else:
                op.tokens[0] = Token.Int(jump, location=op.tokens[0].location)
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


def substitute_label(
    op: AbstractOperation, symbol_table: Dict[str, int]
) -> AbstractOperation:
    """Substitute any label in the instruction with its concrete value."""
    for i, tkn in enumerate(op.tokens):
        if tkn.type == Token.SYMBOL:
            op.tokens[i] = Token.Int(symbol_table[tkn.value], location=tkn.location)
            op.args[i] = symbol_table[tkn.value]
    return op


def labels_to_line_numbers(oplist: List[AbstractOperation]) -> Dict[str, str]:
    """Return a dictionary that maps from label names to their locations in the program,
    as a string of the form "<filepath>:<lineno>".
    """
    labels = {}
    for op in oplist:
        if isinstance(op, LABEL):
            labels[op.args[0]] = "{0.path}:{0.line}".format(op.loc)
    return labels
