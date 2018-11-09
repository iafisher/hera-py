"""Assemble HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
import sys

from .exceptions import AssemblyError
from .parser import Op
from .utils import to_u16


class Assembler:
    def __init__(self):
        self.labels = {}

    def resolve_labels(self, program):
        """Populate the `labels` field with (label, lineno) pairs."""
        pc = 0
        for op in program:
            if op.name.lower() == 'label' and len(op.args) == 1:
                self.labels[op.args[0]] = pc
            else:
                pc += 1

    def assemble(self, program):
        self.resolve_labels(program)

        nprogram = []
        for op in program:
            nprogram.extend(self.assemble_one(op))
        return nprogram

    def assemble_one(self, op):
        try:
            verifier = getattr(self, 'verify_' + op.name.lower())
        except AttributeError:
            pass
        else:
            verifier(self, op.args)

        try:
            handler = getattr(self, 'assemble_' + op.name.lower())
        except AttributeError:
            return [op]
        else:
            return handler(self, *op.args)

    def assemble_set(self, d, v):
        v = to_u16(v)
        if v >> 8 > 0:
            return [Op('SETLO', [d, v & 0xff]), Op('SETHI', [d, v >> 8])]
        else:
            return [Op('SETLO', [d, v & 0xff])]
