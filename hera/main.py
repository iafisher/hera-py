"""hera: an interpreter for the Haverford Educational RISC Architecture.

Usage:
    hera <path>
    hera (-h | --help)
    hera (-v | --version)

Options:
    -h, --help       Show this message.
    -v, --version    Show the version.
"""
import sys

from docopt import docopt

from .parser import parse
from .vm import VirtualMachine


def main():
    arguments = docopt(__doc__, version='hera-py 0.1.0')
    path = arguments['<path>']

    vm = VirtualMachine()

    if path == '-':
        program = sys.stdin.read()
    else:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                program = f.read()
        except FileNotFoundError:
            sys.stderr.write(f'Error: file "{path}" does not exist.\n')
            sys.exit(2)
        except PermissionError:
            sys.stderr.write(f'Error: permission denied to open file "{path}".\n')
            sys.exit(2)
        except OSError:
            sys.stderr.write(f'Error: could not open file "{path}".\n')
            sys.exit(2)

    vm.exec_many(parse(program))
