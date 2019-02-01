from io import StringIO
from unittest.mock import patch

from hera.main import main


def execute_program_helper(program, *, flags=[]):
    with patch("sys.stdin", StringIO(program)):
        return main(flags + ["--no-color", "-"])


def preprocess_program_helper(program):
    with patch("sys.stdin", StringIO(program)):
        main(["preprocess", "--no-color", "-"])
