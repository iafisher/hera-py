"""hera: an interpreter for the Haverford Educational RISC Architecture.

Usage:
    hera [-q | --verbose] [--no-color] [--big-stack] <path>
    hera [--no-color] preprocess <path>
    hera [--no-color] debug <path>
    hera (-h | --help)
    hera (-v | --version)

Options:
    --big-stack      Reserve more space for the stack.
    --verbose        Set output level to verbose.
    -q --quiet       Set output level to quiet.
    --no-color       Do not print colored output.
    -h, --help       Show this message.
    -v, --version    Show the version.
"""
import sys
import functools

from docopt import docopt

from .data import State
from .debugger import debug
from .loader import load_program_from_file
from .utils import op_to_string, print_register_debug
from .vm import VirtualMachine


def external_main(argv=None):
    """A wrapper around main that ignores its return value, so it is not printed to the
    console when the program exits.
    """
    main(argv)


def main(argv=None):
    """The main entry point into hera-py.

    This function consists mostly of argument parsing. The heavy-lifting begins
    with main_execute later in this module.
    """
    arguments = docopt(__doc__, argv=argv, version="hera-py 0.4.0 for HERA version 2.4")
    path = arguments["<path>"]

    state = State()
    if arguments["--no-color"] or not sys.stderr.isatty():
        state.color = False

    if arguments["--big-stack"]:
        # Arbitrary value copied over from HERA-C.
        state.data_start = 0xC167

    if arguments["preprocess"]:
        main_preprocess(path, state)
    elif arguments["debug"]:
        main_debug(path, state)
    else:
        return main_execute(
            path, state, verbose=arguments["--verbose"], quiet=arguments["--quiet"]
        )


def main_debug(path, state):
    """Debug the program."""
    program = load_program_from_file(path, state)
    debug(program)


def main_execute(path, state, *, verbose=False, quiet=False):
    """Execute the program with the given options, most of which correspond to
    command-line arguments.
    """
    program = load_program_from_file(path, state)

    vm = VirtualMachine(state)
    vm.exec_many(program)
    state.warning_count += vm.warning_count

    if not quiet:
        dump_state(vm, state, verbose=verbose)

    return vm


def main_preprocess(path, state):
    """Preprocess the program and print it to standard output."""
    program = load_program_from_file(path, state)
    if program.data:
        sys.stderr.write("[DATA]\n")
        for data_op in program.data:
            sys.stderr.write("  {}\n".format(op_to_string(data_op)))

        if program.code:
            sys.stderr.write("\n[CODE]\n")

    for i, op in enumerate(program.code):
        sys.stderr.write("  {:0>4}  {}\n".format(i, op_to_string(op)))


def dump_state(vm, state, *, verbose=False):
    """Print the state of the virtual machine to standard output."""
    # Make sure that all program output has been printed.
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

    if state.warning_count > 0:
        c = state.warning_count
        nprint("\n{} warning{} emitted.".format(c, "" if c == 1 else "s"))
