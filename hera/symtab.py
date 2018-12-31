from .preprocessor import convert
from .utils import emit_error


# Arbitrary value copied over from HERA-C.
HERA_DATA_START = 0xC001


def get_symtab(program):
    """Return a dictionary mapping all labels and constants to their values."""
    labels = {}
    pc = 0
    dc = HERA_DATA_START
    for op in program:
        odc = dc
        if op.name == "LABEL":
            if len(op.args) == 1:
                update_labels(labels, op.args[0], pc, op)
        elif op.name == "DLABEL":
            if len(op.args) == 1:
                update_labels(labels, op.args[0], dc, op)
        elif op.name == "CONSTANT":
            if len(op.args) == 2:
                update_labels(labels, op.args[0], op.args[1], op)
        elif op.name == "INTEGER":
            dc += 1
        elif op.name == "DSKIP":
            if len(op.args) == 1:
                if isinstance(op.args[0], int):
                    dc += op.args[0]
                elif op.args[0] in labels:
                    dc += labels[op.args[0]]
        elif op.name == "LP_STRING":
            if len(op.args) == 1 and isinstance(op.args[0], str):
                dc += len(op.args[0]) + 1
        else:
            pc += len(convert(op))

        if dc >= 0xFFFF and odc < 0xFFFF:
            emit_error(
                "past the end of available memory", loc=op.location, line=op.name.line
            )
    return labels


def update_labels(labels, k, v, op):
    if k in labels:
        emit_error(
            "symbol `{}` has already been defined".format(k),
            loc=op.location,
            line=op.name.line,
        )
    else:
        labels[k] = v
