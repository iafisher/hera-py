from .preprocessor import convert
from .utils import emit_error


# Arbitrary value copied over from HERA-C.
HERA_DATA_START = 16743


def get_symtab(program):
    """Return a dictionary mapping all labels and constants to their values."""
    labels = {}
    pc = 0
    dc = HERA_DATA_START
    for op in program:
        odc = dc
        if op.name == "LABEL" and len(op.args) == 1:
            labels[op.args[0]] = pc
        elif op.name == "DLABEL" and len(op.args) == 1:
            labels[op.args[0]] = dc
        elif op.name == "CONSTANT" and len(op.args) == 2:
            labels[op.args[0]] = op.args[1]
        elif op.name == "INTEGER":
            dc += 1
        elif op.name == "DSKIP" and len(op.args) == 1 and isinstance(op.args[0], int):
            dc += op.args[0]
        elif (
            op.name == "LP_STRING" and len(op.args) == 1 and isinstance(op.args[0], str)
        ):
            dc += len(op.args[0]) + 1
        else:
            pc += len(convert(op))

        if dc >= 0xFFFF and odc < 0xFFFF:
            emit_error("past the end of available memory", line=op.name.line)
    return labels
