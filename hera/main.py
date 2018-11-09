"""hera: an interpreter for the Haverford Educational RISC Architecture.

Usage:
    hera [--verbose] <path>
    hera (-h | --help)
    hera (-v | --version)

Options:
    -h, --help       Show this message.
    -v, --version    Show the version.
    --verbose        Print verbose output.
"""
import sys

from docopt import docopt

from .assembler import Assembler
from .parser import parse
from .vm import VirtualMachine


def main():
    arguments = docopt(__doc__, version='hera-py 0.1.0')
    path = arguments['<path>']

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

    vm = VirtualMachine()
    assembler = Assembler()
    ops = assembler.assemble(parse(program))

    if '--verbose' in arguments:
        print('Assembled program to:')
        print(deassemble(ops))
        print()

    vm.exec_many(ops)


def deassemble(ops):
    return '\n'.join(deassemble_one(op) for op in ops)


def deassemble_one(op):
    return f"\t{op.name}({', '.join(str(a) for a in op.args)})"
