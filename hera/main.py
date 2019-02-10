"""The command-line entry point into the hera-py system.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import sys
import functools
from typing import Optional

from .data import Settings, VOLUME_QUIET, VOLUME_VERBOSE
from .debugger import debug
from .loader import load_program_from_file
from .utils import format_int
from .vm import VirtualMachine


def external_main(argv=None) -> None:
    """A wrapper around main that ignores its return value, so it is not printed to the
    console when the program exits.
    """
    main(argv)


def main(argv=None) -> Optional[VirtualMachine]:
    """The main entry point into hera-py."""
    arguments = parse_args(argv)
    path = arguments["<path>"]

    settings = Settings()
    if path == "-":
        settings.path = "<stdin>"
    else:
        settings.path = settings.realpath = path

    if arguments["--no-color"] or not sys.stderr.isatty():
        settings.color = False

    if arguments["--big-stack"]:
        # Arbitrary value copied over from HERA-C.
        settings.data_start = 0xC167

    settings.no_debug_ops = arguments["--no-debug-ops"]
    settings.warn_return_on = not arguments["--warn-return-off"]
    settings.warn_octal_on = not arguments["--warn-octal-off"]

    if arguments["--verbose"]:
        settings.volume = VOLUME_VERBOSE
    elif arguments["--quiet"]:
        settings.volume = VOLUME_QUIET

    if arguments["preprocess"]:
        settings.allow_interrupts = True
        main_preprocess(path, settings)
        return None
    elif arguments["debug"]:
        settings.debug = True
        main_debug(path, settings)
        return None
    else:
        return main_execute(path, settings)


def main_debug(path: str, settings: Settings) -> None:
    """Debug the program."""
    program = load_program_from_file(path, settings)
    debug(program, settings)


def main_execute(path: str, settings: Settings) -> VirtualMachine:
    """Execute the program."""
    program = load_program_from_file(path, settings)

    vm = VirtualMachine(settings)
    vm.run(program)
    settings.warning_count += vm.warning_count

    if settings.volume != VOLUME_QUIET:
        dump_state(vm, settings)

    return vm


def main_preprocess(path: str, settings: Settings) -> None:
    """Preprocess the program and print it to standard output."""
    program = load_program_from_file(path, settings)
    if program.data:
        sys.stderr.write("[DATA]\n")
        for data_op in program.data:
            sys.stderr.write("  {}\n".format(data_op))

        if program.code:
            sys.stderr.write("\n[CODE]\n")

    for i, op in enumerate(program.code):
        sys.stderr.write("  {:0>4}  {}\n".format(i, op))


def parse_args(argv):
    if argv is None:
        argv = sys.argv[1:]

    flags = {}
    posargs = []
    after_flags = False
    for arg in argv:
        longarg = short_to_long(arg)
        if longarg == "--":
            after_flags = True
        elif longarg in FLAGS:
            flags[longarg] = True
        elif not after_flags and longarg.startswith("-") and len(longarg) > 1:
            sys.stderr.write("Unrecognized flag: " + arg + "\n")
            sys.exit(1)
        else:
            posargs.append(longarg)

    if "--help" in flags:
        if len(flags) == 1 and not posargs:
            print(HELP)
            sys.exit(0)
        else:
            sys.stderr.write(
                "--help may not be combined with other flags or commands.\n"
            )
            sys.exit(1)

    if "--version" in flags:
        if len(flags) == 1 and not posargs:
            print(VERSION)
            sys.exit(0)
        else:
            sys.stderr.write(
                "--version may not be combined with other flags or commands.\n"
            )
            sys.exit(1)

    if len(posargs) == 0:
        sys.stderr.write("No file path supplied.\n")
        sys.exit(1)
    elif len(posargs) > 1:
        sys.stderr.write("Too many file paths supplied.\n")
        sys.exit(1)

    if "--big-stack" in flags:
        if "preprocess" in flags:
            sys.stderr.write("--big-stack cannot be used with preprocess subcommand.\n")
            sys.exit(1)

    if "--warn-return-off" in flags:
        if "preprocess" in flags:
            sys.stderr.write(
                "--warn-return-off cannot be used with preprocess subcommand.\n"
            )
            sys.exit(1)

    if "--quiet" in flags and "--verbose" in flags:
        sys.stderr.write("--quiet and --verbose are incompatible.\n")
        sys.exit(1)

    flags["<path>"] = posargs[0]
    for f in FLAGS:
        if f not in flags:
            flags[f] = False

    return flags


def short_to_long(arg):
    if arg == "-h":
        return "--help"
    elif arg == "-v":
        return "--version"
    elif arg == "-q":
        return "--quiet"
    else:
        return arg


FLAGS = {
    "--big-stack",
    "--help",
    "--no-color",
    "--no-debug-ops",
    "--quiet",
    "--verbose",
    "--version",
    "--warn-octal-off",
    "--warn-return-off",
    "preprocess",
    "debug",
}
VERSION = "hera-py 0.6.0 for HERA version 2.4"
HELP = """\
hera: an interpreter for the Haverford Educational RISC Architecture.

Usage:
    hera <path>
    hera preprocess <path>
    hera debug <path>

Common options:
    -h, --help         Show this message and exit.
    -v, --version      Show the version and exit.

    --no-color         Do not print colored output.
    --no-debug-ops     Disallow debugging instructions.
    -q --quiet         Set output level to quiet.
    --verbose          Set output level to verbose.
    --warn-octal-off   Do not print warnings for zero-prefixed integer literals.

Interpreter and debugger options:
    --big-stack        Reserve more space for the stack.
    --warn-return-off  Do not print warnings for invalid RETURN addresses.
"""


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
        nprint("{} = {}".format(rname, format_int(value)))

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
