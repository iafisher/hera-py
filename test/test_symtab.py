from hera.parser import Op
from hera.symtab import get_symtab, HERA_DATA_START


def test_get_symtab_with_example():
    labels = get_symtab(
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
    assert len(labels) == 4
    assert labels["data"] == HERA_DATA_START
    assert labels["data2"] == HERA_DATA_START + 2
    assert labels["top"] == 0
    assert labels["bottom"] == 1


def test_get_symtab_with_dskip():
    labels = get_symtab(
        [
            Op("DLABEL", ["data"]),
            Op("INTEGER", [42]),
            Op("DSKIP", [10]),
            Op("DLABEL", ["data2"]),
            Op("INTEGER", [84]),
        ]
    )
    assert len(labels) == 2
    assert labels["data"] == HERA_DATA_START
    assert labels["data2"] == HERA_DATA_START + 11


def test_get_symtab_with_dskip_and_constant():
    labels = get_symtab(
        [
            Op("CONSTANT", ["N", 50]),
            Op("DLABEL", ["x"]),
            Op("DSKIP", ["N"]),  # Using constant value in DSKIP.
            Op("DLABEL", ["y"]),
        ]
    )
    assert len(labels) == 3
    assert labels["N"] == 50
    assert labels["x"] == HERA_DATA_START
    assert labels["y"] == HERA_DATA_START + 50


def test_get_symtab_with_lp_string():
    labels = get_symtab(
        [
            Op("DLABEL", ["S"]),
            Op("LP_STRING", ["hello"]),
            Op("DLABEL", ["X"]),
            Op("INTEGER", [42]),
        ]
    )
    assert len(labels) == 2
    assert labels["S"] == HERA_DATA_START
    assert labels["X"] == HERA_DATA_START + 6


def test_get_symtab_with_empty_lp_string():
    labels = get_symtab(
        [
            Op("DLABEL", ["S"]),
            Op("LP_STRING", [""]),
            Op("DLABEL", ["X"]),
            Op("INTEGER", [42]),
        ]
    )
    assert len(labels) == 2
    assert labels["S"] == HERA_DATA_START
    assert labels["X"] == HERA_DATA_START + 1


def test_get_symtab_with_invalid_instructions():
    labels = get_symtab([Op("CONSTANT", ["N"]), Op("CONSTANT", ["X", 42])])
    assert len(labels) == 1
    assert labels["X"] == 42
