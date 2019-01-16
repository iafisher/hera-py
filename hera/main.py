"""hera: an interpreter for the Haverford Educational RISC Architecture.

Usage:
    hera [-q | --verbose] [--no-color] <path>
    hera [--no-color] preprocess <path>
    hera [--no-color] debug <path>
    hera (-h | --help)
    hera (-v | --version)

Options:
    --verbose        Set output level to verbose.
    -q --quiet       Set output level to quiet.
    --no-color       Do not print colored output.
    -h, --help       Show this message.
    -v, --version    Show the version.
"""
import sys
import functools

from docopt import docopt

from . import config
from .debugger import debug
from .loader import load_program_from_file
from .utils import op_to_string, print_register_debug
from .vm import VirtualMachine


def main(argv=None, vm=None):
    """The main entry point into hera-py.

    This function consists mostly of argument parsing. The heavy-lifting begins
    with main_execute later in this module.

    A virtual machine may be passed in for testing purposes. Otherwise, a new virtual
    machine is created.
    """
    arguments = docopt(__doc__, argv=argv, version="hera-py 0.4.0 for HERA version 2.4")
    path = arguments["<path>"]

    if arguments["--no-color"]:
        config.ANSI_MAGENTA_BOLD = config.ANSI_RED_BOLD = config.ANSI_RESET = ""

    if arguments["preprocess"]:
        main_preprocess(path)
    elif arguments["debug"]:
        main_debug(path)
    else:
        main_execute(
            path, verbose=arguments["--verbose"], quiet=arguments["--quiet"], vm=vm
        )


def main_debug(path):
    """Debug the program."""
    program, symbol_table = load_program_from_file(path)
    debug(program, symbol_table)


def main_execute(path, *, verbose=False, quiet=False, vm=None):
    """Execute the program with the given options, most of which correspond to
    command-line arguments.

    A virtual machine instance may be passed in for testing purposes. If it is not, a
    new one is instantiated. The virtual machine is returned.
    """
    config.WARNING_COUNT = 0

    if vm is None:
        vm = VirtualMachine()

    program, _ = load_program_from_file(path)

    vm.exec_many(program)

    if not quiet:
        dump_state(vm, verbose=verbose)

    return vm


def main_preprocess(path):
    """Preprocess the program and print it to standard output."""
    program, _ = load_program_from_file(path)
    print(program_to_string(program))


def program_to_string(ops):
    """Convert the list of operations to a string."""
    return "\n".join(op_to_string(op) for op in ops)


def dump_state(vm, *, verbose=False):
    """Print the state of the virtual machine to standard output."""
    sys.stdout.flush()

    # Redefine print in this function to use stderr.
    nprint = functools.partial(print, file=sys.stderr)

    if verbose:
        last_register = 15
    else:
        last_register = 10
        while last_register > 0 and vm.registers[last_register] == 0:
            last_register -= 1

    nprint("\nVirtual machine state after execution:")
    for i, value in enumerate(vm.registers[1 : last_register + 1], start=1):
        rname = "\tR" + str(i) + (" " if i < 10 else "")
        print_register_debug(rname, value)

    if last_register > 0:
        nprint()
    else:
        nprint("\tR1 through R10 are all zero.\n")

    flags = [
        vm.flag_carry_block,
        vm.flag_carry,
        vm.flag_overflow,
        vm.flag_zero,
        vm.flag_sign,
    ]
    if not verbose and all(flags):
        nprint("\tAll flags are ON")
    elif not verbose and all(not f for f in flags):
        nprint("\tAll flags are OFF")
    else:
        nprint("\tCarry-block flag is " + ("ON" if vm.flag_carry_block else "OFF"))
        nprint("\tCarry flag is " + ("ON" if vm.flag_carry else "OFF"))
        nprint("\tOverflow flag is " + ("ON" if vm.flag_overflow else "OFF"))
        nprint("\tZero flag is " + ("ON" if vm.flag_zero else "OFF"))
        nprint("\tSign flag is " + ("ON" if vm.flag_sign else "OFF"))

    if config.WARNING_COUNT > 0:
        c = config.WARNING_COUNT
        nprint("\n{} warning{} emitted.".format(c, "" if c == 1 else "s"))
