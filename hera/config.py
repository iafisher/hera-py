"""Global configuration set by the main function."""


# Memory address of the start of the data segment for HERA programs.
HERA_DATA_START = 0xC001


def _make_ansi(*params):
    return "\033[" + ";".join(map(str, params)) + "m"


# ANSI color codes (https://stackoverflow.com/questions/4842424/)
# When the --no-color flag is specified, these constants are set to the empty string, so
# you can use them unconditionally in your code without worrying about --no-color.

ANSI_RED_BOLD = _make_ansi(31, 1)
ANSI_MAGENTA_BOLD = _make_ansi(35, 1)
ANSI_RESET = _make_ansi(0)
