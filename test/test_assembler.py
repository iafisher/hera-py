import pytest
from unittest.mock import patch

from hera.assembler import Assembler
from hera.parser import Op


@pytest.fixture
def asm():
    return Assembler()


def test_resolve_labels_with_small_example(asm):
    program = [
        Op('LABEL', ['TOP_OF_LOOP']),
        Op('CMP', ['R1', 'R0']),
        Op('BZ', ['BOTTOM_OF_LOOP']),
        Op('DEC', ['R1', 1]),
        Op('BR', ['TOP_OF_LOOP']),
        Op('LABEL', ['BOTTOM_OF_LOOP']),
    ]
    asm.resolve_labels(program)
    assert len(asm.labels) == 2
    assert asm.labels['TOP_OF_LOOP'] == 0
    assert asm.labels['BOTTOM_OF_LOOP'] == 4


def test_assemble_set_with_small_positive(asm):
    assert asm.assemble_set('R7', 18) == [Op('SETLO', ['R7', 18])]


def test_assemble_set_with_large_positive(asm):
    assert (
        asm.assemble_set('R7', 34000) == [
            Op('SETLO', ['R7', 208]),
            Op('SETHI', ['R7', 132]),
        ]
    )


def test_assemble_set_with_negative(asm):
    assert (
        asm.assemble_set('R7', -5) == [
            Op('SETLO', ['R7', 251]),
            Op('SETHI', ['R7', 255]),
        ]
    )