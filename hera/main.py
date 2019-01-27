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

from .data import Settings, VOLUME_QUIET, VOLUME_VERBOSE
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

    settings = Settings()
    if arguments["--no-color"] or not sys.stderr.isatty():
        settings.color = False

    if arguments["--big-stack"]:
        # Arbitrary value copied over from HERA-C.
        settings.data_start = 0xC167

    if arguments["--verbose"]:
        settings.volume = VOLUME_VERBOSE
    elif arguments["--quiet"]:
        settings.volume = VOLUME_QUIET

    if arguments["preprocess"]:
        main_preprocess(path, settings)
    elif arguments["debug"]:
        main_debug(path, settings)
    else:
        return main_execute(path, settings)


def main_debug(path, settings):
    """Debug the program."""
    program = load_program_from_file(path, settings)
    debug(program)


def main_execute(path, settings):
    """Execute the program."""
    program = load_program_from_file(path, settings)

    vm = VirtualMachine(settings)
    vm.exec_many(program)
    settings.warning_count += vm.warning_count

    if settings.volume != VOLUME_QUIET:
        dump_state(vm, settings)

    return vm


def main_preprocess(path, settings):
    """Preprocess the program and print it to standard output."""
    program = load_program_from_file(path, settings)
    if program.data:
        sys.stderr.write("[DATA]\n")
        for data_op in program.data:
            sys.stderr.write("  {}\n".format(op_to_string(data_op)))

        if program.code:
            sys.stderr.write("\n[CODE]\n")

    for i, op in enumerate(program.code):
        sys.stderr.write("  {:0>4}  {}\n".format(i, op_to_string(op)))


def dump_state(vm, settings):
    """Print the state of the virtual machine to standard output."""
    # Make sure that all program output has been printed.
    sys.stdout.flush()

    # Redefine print in this function to use stderr.
    nprint = functools.partial(print, file=sys.stderr)

    verbose = settings.volume == VOLUME_VERBOSE
    if verbose:
        last_register = 15
    else:
        last_register = 10
        while last_register > 0 and vm.registers[last_register] == 0:
            last_register -= 1

    nprint("\nVirtual machine state after execution:")
    for i, value in enumerate(vm.registers[1 : last_register + 1], start=1):
        rname = "    R" + str(i) + (" " if i < 10 else "")
        print_register_debug(rname, value)

    if last_register > 0:
        nprint()
    else:
        nprint("    R1 through R10 are all zero.\n")

    flags = [
        vm.flag_carry_block,
        vm.flag_carry,
        vm.flag_overflow,
        vm.flag_zero,
        vm.flag_sign,
    ]
    if not verbose and all(flags):
        nprint("    All flags are ON")
    elif not verbose and all(not f for f in flags):
        nprint("    All flags are OFF")
    else:
        nprint("    Carry-block flag is " + ("ON" if vm.flag_carry_block else "OFF"))
        nprint("    Carry flag is " + ("ON" if vm.flag_carry else "OFF"))
        nprint("    Overflow flag is " + ("ON" if vm.flag_overflow else "OFF"))
        nprint("    Zero flag is " + ("ON" if vm.flag_zero else "OFF"))
        nprint("    Sign flag is " + ("ON" if vm.flag_sign else "OFF"))

    if settings.warning_count > 0:
        c = settings.warning_count
        nprint("\n{} warning{} emitted.".format(c, "" if c == 1 else "s"))
