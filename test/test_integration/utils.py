from io import StringIO
from unittest.mock import patch

from hera.main import main
from hera.vm import VirtualMachine


def execute_program_helper(program):
    with patch("sys.stdin", StringIO(program)):
        return main(["--no-color", "-"])


def preprocess_program_helper(program):
    with patch("sys.stdin", StringIO(program)):
        main(["preprocess", "--no-color", "-"])
