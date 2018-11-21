"""hera: an interpreter for the Haverford Educational RISC Architecture.

Usage:
    hera [options] <path>
    hera [options] preprocess <path>
    hera (-h | --help)
    hera (-v | --version)

Options:
    --dump-state     Print the state of the virtual machine after execution.
    --no-color       Do not print colored output.
    -h, --help       Show this message.
    -v, --version    Show the version.
"""
import sys

from docopt import docopt

from .parser import parse
from .preprocessor import preprocess
from .utils import HERAError
from .vm import VirtualMachine


def main(argv=None, vm=None):
    """The main entry point into hera-py.

    This function consists mostly of argument parsing. The heavy-lifting begins
    with execute_program later in this module.

    A virtual machine instance may be passed in for testing purposes.
    """
    global ANSI_RED_BOLD, ANSI_RESET

    arguments = docopt(__doc__, argv=argv, version="hera-py 0.2.0 for HERA version 2.4")
    path = arguments["<path>"]

    if arguments["--no-color"]:
        ANSI_RED_BOLD = ANSI_RESET = ""

    if path == "-":
        program = sys.stdin.read()
    else:
        try:
            with open(path, "r", encoding="utf-8") as f:
                program = f.read()
        except FileNotFoundError:
            error_and_exit('file "{}" does not exist.\n'.format(path), exitcode=2)
        except PermissionError:
            error_and_exit(
                'permission denied to open file "{}".\n'.format(path), exitcode=2
            )
        except OSError:
            error_and_exit('could not open file "{}".\n'.format(path), exitcode=2)

    # Print a newline if the program came from standard input, so that the
    # program and its output are visually separate.
    if path == "-":
        print()

    if arguments["preprocess"]:
        preprocess_program(program)
    else:
        execute_program(program, opt_dump_state=arguments["--dump-state"], vm=vm)


def execute_program(program, *, opt_dump_state=False, vm=None):
    """Execute the program with the given options, most of which correspond to
    command-line arguments.

    A virtual machine instance may be passed in for testing purposes. If it is not, a
    new one is instantiated. The virtual machine is returned.
    """
    lines = program.splitlines()

    if vm is None:
        vm = VirtualMachine()

    try:
        program = preprocess(parse(program))
        vm.exec_many(program)
    except HERAError as e:
        if e.line:
            if e.column:
                caret = (" " * (e.column + 1)) + "^"
                msg = "{0}, line {0.line} col {0.column}\n\n  {1}\n{2}\n".format(
                    e, lines[e.line - 1], caret
                )
            else:
                msg = "{0}, line {0.line}\n\n  {1}\n".format(e, lines[e.line - 1])
        else:
            msg = str(e)
        error_and_exit(msg)
    else:
        if opt_dump_state:
            dump_state(vm)

        return vm


def preprocess_program(program):
    program = preprocess(parse(program))
    print(program_to_string(program))


def program_to_string(ops):
    """Convert the list of operations to a string."""
    return "\n".join(op_to_string(op) for op in ops)


def op_to_string(op):
    """Convert a single operation to a string."""
    return "{}({})".format(op.name, ", ".join(str(a) for a in op.args))


def dump_state(vm):
    """Print the state of the virtual machine to standard output."""
    print("Virtual machine state:")
    for i, value in enumerate(vm.registers):
        print("\tR{} = {}".format(i, value))
    print()
    print("\tZero flag is " + ("ON" if vm.flag_zero else "OFF"))
    print("\tSign flag is " + ("ON" if vm.flag_sign else "OFF"))
    print("\tOverflow flag is " + ("ON" if vm.flag_overflow else "OFF"))
    print("\tCarry flag is " + ("ON" if vm.flag_carry else "OFF"))
    print("\tCarry block flag is " + ("ON" if vm.flag_carry_block else "OFF"))


def error_and_exit(msg, *, exitcode=3):
    sys.stderr.write(ANSI_RED_BOLD + "Error" + ANSI_RESET + ": ")
    sys.stderr.write(msg + "\n")
    sys.exit(exitcode)


# ANSI color codes (https://stackoverflow.com/questions/4842424/)
# When the --no-color flag is specified, these constants are set to the empty
# string, so they can be used unconditionally in your code but will still obey
# the flag value.


def make_ansi(*params):
    return "\033[" + ";".join(map(str, params)) + "m"


ANSI_RED_BOLD = make_ansi(31, 1)
ANSI_RESET = make_ansi(0)
