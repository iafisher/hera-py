from io import StringIO
from unittest.mock import patch

from hera.main import main
from hera.vm import VirtualMachine


def execute_program_helper(program):
    vm = VirtualMachine()
    with patch("sys.stdin", StringIO(program)):
        main(["--no-color", "-"], vm)
    return vm
