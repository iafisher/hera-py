import pytest

from lark import Token

from hera.parser import Op
from hera.preprocessor import preprocess, Preprocessor, HERA_DATA_START


@pytest.fixture
def ppr():
    return Preprocessor()


def test_preprocess1_set_with_small_positive(ppr):
    assert ppr.preprocess1_set('R5', 18) == [Op('SETLO', ['R5', 18])]


def test_preprocess1_set_with_large_positive(ppr):
    assert ppr.preprocess1_set('R5', 34000) == [
        Op('SETLO', ['R5', 208]),
        Op('SETHI', ['R5', 132]),
    ]


def test_preprocess1_set_with_negative(ppr):
    assert ppr.preprocess1_set('R5', -5) == [
        Op('SETLO', ['R5', 251]),
        Op('SETHI', ['R5', 255]),
    ]


def test_preprocess1_set_with_symbol(ppr):
    assert ppr.preprocess1_set('R5', 'whatever') == [
        Op('SETLO', ['R5', 'whatever']),
        Op('SETHI', ['R5', 'whatever']),
    ]


def test_preprocess1_move(ppr):
    assert ppr.preprocess1_move('R5', 'R3') == [Op('OR', ['R5', 'R3', 'R0'])]


def test_preprocess1_con(ppr):
    assert ppr.preprocess1_con() == [Op('FON', [8])]


def test_preprocess1_coff(ppr):
    assert ppr.preprocess1_coff() == [Op('FOFF', [8])]


def test_preprocess1_cbon(ppr):
    assert ppr.preprocess1_cbon() == [Op('FON', [16])]


def test_preprocess1_ccboff(ppr):
    assert ppr.preprocess1_ccboff() == [Op('FOFF', [24])]


def test_preprocess2_label(ppr):
    assert ppr.preprocess2_label('whatever') is None


def test_preprocess2_dlabel(ppr):
    assert ppr.preprocess2_dlabel('whatever') is None


def test_preprocess2_constant(ppr):
    assert ppr.preprocess2_constant('whatever', 5) is None


def test_preprocess1_cmp(ppr):
    assert ppr.preprocess1_cmp('R1', 'R2') == [
        Op('FON', [8]),
        Op('SUB', ['R0', 'R1', 'R2']),
    ]


def test_preprocess1_setrf_with_small_positive(ppr):
    assert ppr.preprocess1_setrf('R5', 18) == [
        Op('SETLO', ['R5', 18]),
        Op('FOFF', [8]),
        Op('ADD', ['R0', 'R5', 'R0']),
    ]


def test_preprocess1_setrf_with_large_positive(ppr):
    assert ppr.preprocess1_setrf('R5', 34000) == [
        Op('SETLO', ['R5', 208]),
        Op('SETHI', ['R5', 132]),
        Op('FOFF', [8]),
        Op('ADD', ['R0', 'R5', 'R0']),
    ]


def test_preprocess1_setrf_with_negative(ppr):
    assert ppr.preprocess1_setrf('R5', -5) == [
        Op('SETLO', ['R5', 251]),
        Op('SETHI', ['R5', 255]),
        Op('FOFF', [8]),
        Op('ADD', ['R0', 'R5', 'R0']),
    ]


def test_preprocess1_flags(ppr):
    assert ppr.preprocess1_flags('R8') == [
        Op('FOFF', [8]),
        Op('ADD', ['R0', 'R8', 'R0'])
    ]


def test_preprocess1_br_with_register(ppr):
    assert ppr.preprocess1_br(Token('REGISTER', 'R5')) == [Op('BR', ['R5'])]


def test_preprocess1_br_with_label(ppr):
    assert ppr.preprocess1_br(Token('SYMBOL', 'top')) == [
        Op('SETLO', ['R11', 'top']),
        Op('SETHI', ['R11', 'top']),
        Op('BR', ['R11'])
    ]


def test_preprocess1_halt(ppr):
    assert ppr.preprocess1_halt() == [Op('BRR', [0])]


def test_preprocess1_nop(ppr):
    assert ppr.preprocess1_nop() == [Op('BRR', [1])]


def test_preprocess1_call_with_register(ppr):
    assert ppr.preprocess1_call('R12', Token('REGISTER', 'R13')) == [
        Op('CALL', ['R12', 'R13'])
    ]


def test_preprocess1_call_with_label(ppr):
    assert ppr.preprocess1_call('R12', Token('SYMBOL', 'div')) == [
        Op('SETLO', ['R13', 'div']),
        Op('SETHI', ['R13', 'div']),
        Op('CALL', ['R12', 'R13']),
    ]


def test_preprocess1_neg(ppr):
    assert ppr.preprocess1_neg('R1', 'R2') == [
        Op('FON', [8]),
        Op('SUB', ['R1', 'R0', 'R2']),
    ]


def test_preprocess1_not(ppr):
    assert ppr.preprocess1_not('R1', 'R2') == [
        Op('SETLO', ['R11', 0xff]),
        Op('SETHI', ['R11', 0xff]),
        Op('XOR', ['R1', 'R11', 'R2']),
    ]


def test_resolve_labels_with_example(ppr):
    ppr.resolve_labels([
        Op('DLABEL', ['data']),
        Op('INTEGER', [42]),
        Op('INTEGER', [43]),
        Op('DLABEL', ['data2']),
        Op('INTEGER', [100]),
        Op('LABEL', ['top']),
        Op('ADD', ['R0', 'R0', 'R0']),
        Op('LABEL', ['bottom']),
    ])
    assert len(ppr.labels) == 4
    assert ppr.labels['data'] == HERA_DATA_START
    assert ppr.labels['data2'] == HERA_DATA_START + 2
    assert ppr.labels['top'] == 0
    assert ppr.labels['bottom'] == 1


def test_resolve_labels_with_dskip(ppr):
    ppr.resolve_labels([
        Op('DLABEL', ['data']),
        Op('INTEGER', [42]),
        Op('DSKIP', [10]),
        Op('DLABEL', ['data2']),
        Op('INTEGER', [84]),
    ])
    assert len(ppr.labels) == 2
    assert ppr.labels['data'] == HERA_DATA_START
    assert ppr.labels['data2'] == HERA_DATA_START + 11


def test_resolve_labels_with_lp_string(ppr):
    ppr.resolve_labels([
        Op('DLABEL', ['S']),
        Op('LP_STRING', ['hello']),
        Op('DLABEL', ['X']),
        Op('INTEGER', [42]),
    ])
    assert len(ppr.labels) == 2
    assert ppr.labels['S'] == HERA_DATA_START
    assert ppr.labels['X'] == HERA_DATA_START + 6


def test_resolve_labels_with_empty_lp_string(ppr):
    ppr.resolve_labels([
        Op('DLABEL', ['S']),
        Op('LP_STRING', ['']),
        Op('DLABEL', ['X']),
        Op('INTEGER', [42]),
    ])
    assert len(ppr.labels) == 2
    assert ppr.labels['S'] == HERA_DATA_START
    assert ppr.labels['X'] == HERA_DATA_START + 1


def test_assemble_constant(ppr):
    program = [
        Op('CONSTANT', ['n', 100]), Op('SET', ['R1', Token('SYMBOL', 'n')])
    ]
    assert preprocess(program) == [
        Op('SETLO', ['R1', 100]), Op('SETHI', ['R1', 0])
    ]
