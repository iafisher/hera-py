from hera.data import Op, Token
from hera.symtab import get_symbol_table, HERA_DATA_START


def SYM(s):
    return Token("SYMBOL", s)


def test_get_symbol_table_with_example():
    symbol_table, errors = get_symbol_table(
        [
            Op("DLABEL", ["data"]),
            Op("INTEGER", [42]),
            Op("INTEGER", [43]),
            Op("DLABEL", ["data2"]),
            Op("INTEGER", [100]),
            Op("LABEL", ["top"]),
            Op("ADD", ["R0", "R0", "R0"]),
            Op("LABEL", ["bottom"]),
        ]
    )

    assert not errors
    assert len(symbol_table) == 4
    assert symbol_table["data"] == HERA_DATA_START
    assert symbol_table["data2"] == HERA_DATA_START + 2
    assert symbol_table["top"] == 0
    assert symbol_table["bottom"] == 1


def test_get_symbol_table_with_dskip():
    symbol_table, errors = get_symbol_table(
        [
            Op("DLABEL", ["data"]),
            Op("INTEGER", [42]),
            Op("DSKIP", [10]),
            Op("DLABEL", ["data2"]),
            Op("INTEGER", [84]),
        ]
    )

    assert not errors
    assert len(symbol_table) == 2
    assert symbol_table["data"] == HERA_DATA_START
    assert symbol_table["data2"] == HERA_DATA_START + 11


def test_get_symbol_table_with_dskip_and_constant():
    symbol_table, errors = get_symbol_table(
        [
            Op("CONSTANT", ["N", 50]),
            Op("DLABEL", ["x"]),
            Op("DSKIP", ["N"]),  # Using constant value in DSKIP.
            Op("DLABEL", ["y"]),
        ]
    )

    assert not errors
    assert len(symbol_table) == 3
    assert symbol_table["N"] == 50
    assert symbol_table["x"] == HERA_DATA_START
    assert symbol_table["y"] == HERA_DATA_START + 50


def test_get_symbol_table_with_lp_string():
    symbol_table, errors = get_symbol_table(
        [
            Op("DLABEL", ["S"]),
            Op("LP_STRING", ["hello"]),
            Op("DLABEL", ["X"]),
            Op("INTEGER", [42]),
        ]
    )

    assert not errors
    assert len(symbol_table) == 2
    assert symbol_table["S"] == HERA_DATA_START
    assert symbol_table["X"] == HERA_DATA_START + 6


def test_get_symbol_table_with_empty_lp_string():
    symbol_table, errors = get_symbol_table(
        [
            Op("DLABEL", ["S"]),
            Op("LP_STRING", [""]),
            Op("DLABEL", ["X"]),
            Op("INTEGER", [42]),
        ]
    )

    assert not errors
    assert len(symbol_table) == 2
    assert symbol_table["S"] == HERA_DATA_START
    assert symbol_table["X"] == HERA_DATA_START + 1


def test_get_symbol_table_with_invalid_instructions():
    symbol_table, errors = get_symbol_table(
        [Op("CONSTANT", ["N"]), Op("CONSTANT", ["X", 42])]
    )

    assert not errors
    assert len(symbol_table) == 1
    assert symbol_table["X"] == 42


def test_get_symbol_table_with_too_large_dskip(capsys):
    get_symbol_table([Op(SYM("DSKIP"), [1000000000])])

    assert "past the end of available memory" in capsys.readouterr().err


def test_get_symbol_table_with_redefinitions_of_symbols(capsys):
    get_symbol_table(
        [
            Op(SYM("CONSTANT"), ["A", 100]),
            Op(SYM("CONSTANT"), ["B", 200]),
            Op(SYM("CONSTANT"), ["C", 200]),
            Op(SYM("CONSTANT"), ["A", -1]),
            Op(SYM("LABEL"), ["B"]),
            Op(SYM("DLABEL"), ["C"]),
        ]
    )

    captured = capsys.readouterr().err

    assert "symbol `A` has already been defined" in captured
    assert "symbol `B` has already been defined" in captured
    assert "symbol `C` has already been defined" in captured
