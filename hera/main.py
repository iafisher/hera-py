import sys
import functools

from .data import Settings, VOLUME_QUIET, VOLUME_VERBOSE
from .debugger import debug
from .loader import load_program_from_file
from .utils import format_int
from .vm import VirtualMachine


def external_main(argv=None):
    """A wrapper around main that ignores its return value, so it is not printed to the
    console when the program exits.
    """
    main(argv)


def main(argv=None):
    """The main entry point into hera-py."""
    arguments = parse_args(argv)
    path = arguments["<path>"]

    settings = Settings()
    if arguments["--no-color"] or not sys.stderr.isatty():
        settings.color = False

    if arguments["--big-stack"]:
        # Arbitrary value copied over from HERA-C.
        settings.data_start = 0xC167

    if arguments["--no-debug"]:
        settings.no_debug = True

    if arguments["--no-ret-warn"]:
        settings.no_ret_warn = True

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
    debug(program, settings)


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
    "--no-debug",
    "--no-ret-warn",
    "--quiet",
    "--verbose",
    "--version",
    "preprocess",
    "debug",
}
VERSION = "hera-py 0.5.1 for HERA version 2.4"
HELP = """\
hera: an interpreter for the Haverford Educational RISC Architecture.

Usage:
    hera <path>
    hera preprocess <path>
    hera debug <path>

Common options:
    -h, --help       Show this message and exit.
    --no-color       Do not print colored output.
    -v, --version    Show the version and exit.

Execution options:
    --big-stack      Reserve more space for the stack.
    --no-debug       Disallow debugging instructions.
    --no-ret-warn    Do not print warnings for invalid RETURN addresses.
    -q --quiet       Set output level to quiet.
    --verbose        Set output level to verbose.
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
