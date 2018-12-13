from hera.config import _make_ansi


def test_make_ansi_red():
    assert _make_ansi(31, 1) == "\033[31;1m"


def test_make_ansi_reset():
    assert _make_ansi(0) == "\033[0m"
