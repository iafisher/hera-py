"""The HERA assembler.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: March 2019
"""
import textwrap
from typing import List, Tuple

from .data import Program, Settings


def assemble(program: Program) -> Tuple[List[bytes], List[bytes]]:
    code = []
    data = []

    for op in program.code:
        code.append(op.assemble())

    for data_op in program.data:
        data.append(data_op.assemble())

    return (code, data)


def assemble_and_print(program: Program, settings: Settings) -> None:
    raw_code, raw_data = assemble(program)

    code = "\n".join(bytes_to_hex(b) for b in raw_code)

    raw_data_concat = b"".join(raw_data)
    datalist = []
    for i in range(0, len(raw_data_concat), 2):
        hi = raw_data_concat[i]
        lo = raw_data_concat[i + 1]
        datalist.append("{:x}".format((hi << 8) + lo))
    data = "\n".join(datalist)
    # I don't know what the significance of this cell is, but Hassem includes it.
    cell = (len(raw_data_concat) // 2) + settings.data_start
    data = "{:x}\n".format(cell) + data
    # Make sure to put zeroes up to the start of the data segment.
    data = "{}*0\n".format(settings.data_start - 1) + data

    if settings.stdout:
        if settings.data:
            print(data)
        elif settings.code:
            print(code)
        else:
            print("[DATA]")
            print(textwrap.indent(data, "  "))
            print("[CODE]")
            print(textwrap.indent(code, "  "))
    else:
        if settings.path == "-":
            path = "stdin"
        else:
            path = settings.path

        with open(path + ".lcode", "w", encoding="ascii") as f:
            f.write(code)
            f.write("\n")

        with open(path + ".ldata", "w", encoding="ascii") as f:
            f.write(data)


def bytes_to_hex(b: bytes) -> str:
    try:
        return b.hex()
    except AttributeError:
        # bytes.hex is not implemented in Python 3.4.
        return "".join("{:0>2x}".format(c) for c in b)
