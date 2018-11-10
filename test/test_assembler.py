import pytest

from lark import Token

from hera.assembler import AssemblyHelper, HERA_DATA_START
from hera.parser import Op


@pytest.fixture
def asm():
    return AssemblyHelper()


def test_assemble1_set_with_small_positive(asm):
    assert asm.assemble1_set('R5', 18) == [Op('SETLO', ['R5', 18])]


def test_assemble1_set_with_large_positive(asm):
    assert asm.assemble1_set('R5', 34000) == [
        Op('SETLO', ['R5', 208]),
        Op('SETHI', ['R5', 132]),
    ]


def test_assemble1_set_with_negative(asm):
    assert asm.assemble1_set('R5', -5) == [
        Op('SETLO', ['R5', 251]),
        Op('SETHI', ['R5', 255]),
    ]


def test_assemble1_set_with_symbol(asm):
    assert asm.assemble1_set('R5', 'whatever') == [
        Op('SETLO', ['R5', 'whatever']),
        Op('SETHI', ['R5', 'whatever']),
    ]


def test_assemble1_move(asm):
    assert asm.assemble1_move('R5', 'R3') == [Op('OR', ['R5', 'R3', 'R0'])]


def test_assemble1_con(asm):
    assert asm.assemble1_con() == [Op('FON', [8])]


def test_assemble1_coff(asm):
    assert asm.assemble1_coff() == [Op('FOFF', [8])]


def test_assemble1_cbon(asm):
    assert asm.assemble1_cbon() == [Op('FON', [16])]


def test_assemble1_ccboff(asm):
    assert asm.assemble1_ccboff() == [Op('FOFF', [24])]


def test_assemble2_label(asm):
    assert asm.assemble2_label('whatever') is None


def test_assemble2_dlabel(asm):
    assert asm.assemble2_dlabel('whatever') is None


def test_assemble1_cmp(asm):
    assert asm.assemble1_cmp('R1', 'R2') == [
        Op('FON', [8]),
        Op('SUB', ['R0', 'R1', 'R2']),
    ]


def test_assemble1_setrf_with_small_positive(asm):
    assert asm.assemble1_setrf('R5', 18) == [
        Op('SETLO', ['R5', 18]),
        Op('FOFF', [8]),
        Op('ADD', ['R0', 'R5', 'R0']),
    ]


def test_assemble1_setrf_with_large_positive(asm):
    assert asm.assemble1_setrf('R5', 34000) == [
        Op('SETLO', ['R5', 208]),
        Op('SETHI', ['R5', 132]),
        Op('FOFF', [8]),
        Op('ADD', ['R0', 'R5', 'R0']),
    ]


def test_assemble1_setrf_with_negative(asm):
    assert asm.assemble1_setrf('R5', -5) == [
        Op('SETLO', ['R5', 251]),
        Op('SETHI', ['R5', 255]),
        Op('FOFF', [8]),
        Op('ADD', ['R0', 'R5', 'R0']),
    ]


def test_assemble1_flags(asm):
    assert asm.assemble1_flags('R8') == [
        Op('FOFF', [8]),
        Op('ADD', ['R0', 'R8', 'R0'])
    ]


def test_assemble1_br_with_register(asm):
    assert asm.assemble1_br(Token('REGISTER', 'R5')) == [Op('BR', ['R5'])]


def test_assemble1_br_with_label(asm):
    assert asm.assemble1_br(Token('SYMBOL', 'top')) == [
        Op('SETLO', ['R11', 'top']),
        Op('SETHI', ['R11', 'top']),
        Op('BR', ['R11'])
    ]


def test_assemble1_halt(asm):
    assert asm.assemble1_halt() == [Op('BRR', [0])]


def test_assemble1_nop(asm):
    assert asm.assemble1_nop() == [Op('BRR', [1])]


def test_assemble1_call_with_register(asm):
    assert asm.assemble1_call('R12', Token('REGISTER', 'R13')) == [
        Op('CALL', ['R12', 'R13'])
    ]


def test_assemble1_call_with_label(asm):
    assert asm.assemble1_call('R12', Token('SYMBOL', 'div')) == [
        Op('SETLO', ['R13', 'div']),
        Op('SETHI', ['R13', 'div']),
        Op('CALL', ['R12', 'R13']),
    ]


def test_assemble1_neg(asm):
    assert asm.assemble1_neg('R1', 'R2') == [
        Op('FON', [8]),
        Op('SUB', ['R1', 'R0', 'R2']),
    ]


def test_assemble1_not(asm):
    assert asm.assemble1_not('R1', 'R2') == [
        Op('SETLO', ['R11', 0xff]),
        Op('SETHI', ['R11', 0xff]),
        Op('XOR', ['R1', 'R11', 'R2']),
    ]


def test_resolve_labels_with_example(asm):
    asm.resolve_labels([
        Op('DLABEL', ['data']),
        Op('INTEGER', [42]),
        Op('INTEGER', [43]),
        Op('DLABEL', ['data2']),
        Op('INTEGER', [100]),
        Op('LABEL', ['top']),
        Op('ADD', ['R0', 'R0', 'R0']),
        Op('LABEL', ['bottom']),
    ])
    assert len(asm.labels) == 4
    assert asm.labels['data'] == HERA_DATA_START
    assert asm.labels['data2'] == HERA_DATA_START + 2
    assert asm.labels['top'] == 0
    assert asm.labels['bottom'] == 1


def test_resolve_labels_with_dskip(asm):
    asm.resolve_labels([
        Op('DLABEL', ['data']),
        Op('INTEGER', [42]),
        Op('DSKIP', [10]),
        Op('DLABEL', ['data2']),
        Op('INTEGER', [84]),
    ])
    assert len(asm.labels) == 2
    assert asm.labels['data'] == HERA_DATA_START
    assert asm.labels['data2'] == HERA_DATA_START + 11
