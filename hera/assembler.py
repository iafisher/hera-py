"""Assemble HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
from lark import Token

from .parser import Op
from .utils import to_u16


def assemble(program):
    """Assemble the program (a list of Op objects) into valid input for the
    exec_many method on the VirtualMachine class.

    This function does the following
        - Replaces pseudo-instructions with real ones
        - Verifies the correct usage of instructions
        - Resolves labels into their line numbers.
    """
    helper = AssemblyHelper()
    return helper.assemble(program)


def branch_assembler(name):
    """A factory method to create handlers for branch instructions. All of these
    receive the same first-pass translation, which replaces the use of a label
    with a SET(R11, label) BRANCH(R11) combination.
    """
    def assemble1_XXX(self, l):
        if isinstance(l, Token) and l.type == 'SYMBOL':
            # Note that we MUST use SETLO+SETHI and not SET, because the next
            # pass only handles label resolution and does not further expand
            # pseudo-instructions.
            return [
                Op('SETLO', ['R11', l]),
                Op('SETHI', ['R11', l]),
                Op(name, ['R11'])
            ]
        else:
            return [Op(name, [l])]

    return assemble1_XXX


class AssemblyHelper:
    """A helper class for assembling programs. Do not instantiate this class
    directly. Use the module-level assemble function instead.
    """

    def __init__(self):
        self.labels = {}

    def assemble(self, program):
        """See docstring for module-level assemble for details."""
        for op in program:
            try:
                verifier = getattr(self, 'verify_' + op.name.lower())
            except AttributeError:
                pass
            else:
                verifier(*op.args)

        program = self.assemble_first_pass(program)
        program = self.assemble_second_pass(program)
        return program

    def assemble_first_pass(self, program):
        """Run the first pass of the assembler. This pass converts pseudo-
        instructions to real ones, but does not resolve labels. It does however
        guarantee that labels will only appear as the second argument of SETLO
        and SETHI.
        """
        nprogram = []
        for op in program:
            try:
                handler = getattr(self, 'assemble1_' + op.name.lower())
            except AttributeError:
                nprogram.append(op)
            else:
                nprogram.extend(handler(*op.args))
        return nprogram

    def assemble_second_pass(self, program):
        """Run the second pass of the assembler. This pass resolves labels into
        their actual line numbers. It assumes that labels only appear as the
        second argument of SETLO and SETHI (the assemble_first_pass method
        guarantees this).
        """
        pc = 0
        for op in program:
            if op.name.lower() == 'label':
                self.labels[op.args[0]] = pc
            else:
                pc += 1

        nprogram = []
        for op in program:
            try:
                handler = getattr(self, 'assemble2_' + op.name.lower())
            except AttributeError:
                nprogram.append(op)
            else:
                nop = handler(*op.args)
                if nop:
                    nprogram.append(nop)
        return nprogram

    def assemble1_set(self, d, v):
        v = to_u16(v)
        lo = v & 0xff
        hi = v >> 8
        if hi:
            return [
                Op('SETLO', [d, lo]),
                Op('SETHI', [d, hi]),
            ]
        else:
            return [Op('SETLO', [d, lo])]

    def assemble1_cmp(self, a, b):
        return [Op('FON', [8]), Op('SUB', ['R0', a, b])]

    def assemble1_con(self):
        return [Op('FON', [8])]

    def assemble1_coff(self):
        return [Op('FOFF', [8])]

    def assemble1_cbon(self):
        return [Op('FON', [16])]

    def assemble1_ccboff(self):
        return [Op('FOFF', [24])]

    def assemble1_move(self, a, b):
        return [Op('OR', [a, b, 'R0'])]

    def assemble1_setrf(self, d, v):
        return self.assemble1_set(d, v) + self.assemble1_flags(d)

    def assemble1_flags(self, a):
        return [Op('FOFF', [8]), Op('ADD', ['R0', a, 'R0'])]

    def assemble1_halt(self):
        return [Op('BRR', [0])]

    def assemble1_nop(self):
        return [Op('BRR', [1])]

    def assemble1_call(self, a, l):
        if isinstance(l, Token) and l.type == 'SYMBOL':
            return [
                Op('SETLO', ['R13', l]),
                Op('SETHI', ['R13', l]),
                Op('CALL', [a, 'R13']),
            ]
        else:
            return [Op('CALL', [a, l])]

    # Assembling branch instructions. Read the docstring of branch_assembler
    # for details.
    assemble1_br = branch_assembler('BR')
    assemble1_bl = branch_assembler('BL')
    assemble1_bge = branch_assembler('BGE')
    assemble1_ble = branch_assembler('BLE')
    assemble1_bg = branch_assembler('BG')
    assemble1_bule = branch_assembler('BULE')
    assemble1_bug = branch_assembler('BUG')
    assemble1_bz = branch_assembler('BZ')
    assemble1_bnz = branch_assembler('BNZ')
    assemble1_bc = branch_assembler('BC')
    assemble1_bnc = branch_assembler('BNC')
    assemble1_bs = branch_assembler('BS')
    assemble1_bns = branch_assembler('BNS')
    assemble1_bv = branch_assembler('BV')
    assemble1_bnv = branch_assembler('BNV')

    def assemble2_label(self, l):
        # Labels do not result in any machine code instructions.
        return None

    def assemble2_setlo(self, d, v):
        # We must handle the case where the second argument of SETLO is a label.
        if isinstance(v, Token) and v.type == 'SYMBOL':
            return Op('SETLO', [d, self.labels[v] & 0xff])
        else:
            return Op('SETLO', [d, v])

    def assemble2_sethi(self, d, v):
        # We must handle the case where the second argument of SETHI is a label.
        if isinstance(v, Token) and v.type == 'SYMBOL':
            return Op('SETHI', [d, self.labels[v] >> 8])
        else:
            return Op('SETHI', [d, v])
