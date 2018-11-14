"""hera: an interpreter for the Haverford Educational RISC Architecture.

Usage:
    hera [--verbose --dump-state] <path>
    hera preprocess <path>
    hera (-h | --help)
    hera (-v | --version)

Options:
    --dump-state     Print the state of the virtual machine after execution.
    -h, --help       Show this message.
    -v, --version    Show the version.
"""
import sys

from docopt import docopt

from .parser import parse
from .preprocessor import preprocess
from .vm import VirtualMachine


def main(argv=None):
    """The main entry point into hera-py.

    This function consists mostly of argument parsing. The heavy-lifting begins
    with execute_program later in this module.
    """
    arguments = docopt(
        __doc__, argv=argv, version='hera-py 0.2.0 for HERA version 2.4'
    )
    path = arguments['<path>']

    if path == '-':
        program = sys.stdin.read()
    else:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                program = f.read()
        except FileNotFoundError:
            sys.stderr.write('Error: file "{}" does not exist.\n'.format(path))
            sys.exit(2)
        except PermissionError:
            sys.stderr.write(
                'Error: permission denied to open file "{}".\n'.format(path)
            )
            sys.exit(2)
        except OSError:
            sys.stderr.write('Error: could not open file "{}".\n'.format(path))
            sys.exit(2)

    # Print a newline if the program came from standard input, so that the
    # program and its output are visually separate.
    if path == '-':
        print()

    if arguments['preprocess']:
        preprocess_program(program)
    else:
        execute_program(
            program,
            opt_dump_state=arguments['--dump-state']
        )


def execute_program(program, *, opt_dump_state=False):
    """Execute the program with the given options, most of which correspond to
    command-line arguments.

    The virtual machine instance that this function instantiates to run the
    program is returned, primarily so that integration tests can check its
    state.
    """
    vm = VirtualMachine()
    program = preprocess(parse(program))

    vm.exec_many(program)

    if opt_dump_state:
        dump_state(vm)

    return vm


def preprocess_program(program):
    program = preprocess(parse(program))
    print(program_to_string(program))


def program_to_string(ops):
    """Convert the list of operations to a string."""
    return '\n'.join(op_to_string(op) for op in ops)


def op_to_string(op):
    """Convert a single operation to a string."""
    return "{}({})".format(
        op.name,
        ', '.join(str(a) for a in op.args),
    )


def dump_state(vm):
    """Print the state of the virtual machine to standard output."""
    print('Virtual machine state:')
    for i, value in enumerate(vm.registers):
        print('\tR{} = {}'.format(i, value))
    print()
    print('\tZero flag is ' + ('ON' if vm.flag_zero else 'OFF'))
    print('\tSign flag is ' + ('ON' if vm.flag_sign else 'OFF'))
    print('\tOverflow flag is ' + ('ON' if vm.flag_overflow else 'OFF'))
    print('\tCarry flag is ' + ('ON' if vm.flag_carry else 'OFF'))
    print('\tCarry block flag is ' + ('ON' if vm.flag_carry_block else 'OFF'))
