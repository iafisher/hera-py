"""Global configuration set by the main function."""

# The lines of the program being processed (a list of strings). Used for error messages.
LINES = None


# Number of errors and warnings emitted.
ERROR_COUNT = 0
WARNING_COUNT = 0


def _make_ansi(*params):
    return "\033[" + ";".join(map(str, params)) + "m"


# ANSI color codes (https://stackoverflow.com/questions/4842424/)
# When the --no-color flag is specified, these constants are set to the empty string, so
# they can be used unconditionally in your code but will still obey the flag value.

ANSI_RED_BOLD = _make_ansi(31, 1)
ANSI_MAGENTA_BOLD = _make_ansi(35, 1)
ANSI_RESET = _make_ansi(0)
