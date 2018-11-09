"""Assemble HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
import sys

from .exceptions import AssemblyError
from .parser import Op
from .utils import to_u16


class Assembler:
    """A class to convert pseudo-instructions and to statically verify HERA
    assembly programs.
    """

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
        """Verify all instructions and replace pseudo-instructions with real
        ones.
        """
        self.resolve_labels(program)

        nprogram = []
        for op in program:
            nprogram.extend(self.assemble_one(op))

        return nprogram

    def assemble_one(self, op):
        """Convert a single operation. The return value is a list of
        corresponding operations (since some pseudo-instructions map to
        multiple machine instructions).
        """
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
            return handler(*op.args)

    def assemble_set(self, d, v):
        """Assemble the SET instruction, into a pair of SETLO and SETHI calls.
        """
        v = to_u16(v)
        if v >> 8 > 0:
            return [Op('SETLO', [d, v & 0xff]), Op('SETHI', [d, v >> 8])]
        else:
            return [Op('SETLO', [d, v & 0xff])]
