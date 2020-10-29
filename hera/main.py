"""
The command-line entry point into hera-py.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: July 2019
"""
import functools
import sys

from .assembler import assemble_and_print
from .data import HERAError, Settings, VOLUME_QUIET, VOLUME_VERBOSE
from .debugger import debug
from .loader import load_program_from_file
from .op import disassemble
from .utils import format_int, Path, read_file_or_stdin, register_to_index
from .vm import VirtualMachine


VERSION = "hera-py 1.0.3 for HERA version 2.4"


def external_main(argv=None) -> None:
    """
    A wrapper around main that ignores its return value, which would otherwise be
    printed to the console on program exit.
    """
    main(argv)


def main(argv: "Optional[List[str]]" = None) -> "Optional[VirtualMachine]":
    """
    The entry point into hera-py.

    If the interpeter subcommand is executed, the virtual machine on which the program
    is run is returned so that its internal state may be inspected for testing.
    """
    settings = parse_args(argv)
    if settings.path == "-":
        path = Path("<stdin>", kind=Path.STDIN)
    else:
        path = Path(settings.path)

    if not sys.stderr.isatty():
        settings.color = False

    if settings.mode == "preprocess":
        settings.allow_interrupts = True
        main_preprocess(path, settings)
        return None
    elif settings.mode == "debug":
        main_debug(path, settings)
        return None
    elif settings.mode == "assemble":
        settings.allow_interrupts = True
        main_assemble(path, settings)
        return None
    elif settings.mode == "disassemble":
        main_disassemble(path, settings)
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

    # Check if the program exited prematurely due to throttling.
    if settings.throttle is not False and vm.op_count == settings.throttle:
        sys.stderr.write(
            "Program throttled after {} instructions.\n".format(vm.op_count)
        )

    settings.warning_count += vm.warning_count

    if settings.volume != VOLUME_QUIET:
        dump_state(vm, settings)

    return vm


def main_preprocess(path: str, settings: Settings) -> None:
    """Preprocess the program and print it to stdout."""
    program = load_program_from_file(path, settings)

    if not settings.obfuscate:
        if program.data:
            print("[DATA]")
            for data_op in program.data:
                print("  {}".format(data_op))

            if program.code:
                print("\n[CODE]")

        for i, op in enumerate(program.code):
            print("  {:0>4}  {}".format(i, op))
    else:
        for data_op in program.data:
            print("{}".format(data_op))

        for i, op in enumerate(program.code):
            assembled = op.assemble()
            v = (assembled[0] << 8) + assembled[1]
            print("OPCODE(0x{:x})".format(v))


def main_assemble(path: str, settings: Settings) -> None:
    """Assemble the program into machine code and print the hex output to stdout."""
    program = load_program_from_file(path, settings)
    assemble_and_print(program, settings)


def main_disassemble(path: str, settings: Settings) -> None:
    """
    Disassemble the machine code (expressed as newline-separated hex numbers, without
    the "0x" prefix), and print the HERA output to stdout.
    """
    text = read_file_or_stdin(path, settings)
    for line in text.splitlines():
        try:
            v = int(line, base=16)
        except ValueError:
            print("// Invalid hex literal: {}".format(line))
            continue

        try:
            print(disassemble(v))
        except HERAError:
            print("// Unknown instruction: {}".format(line))


def parse_args(argv: "Optional[List[str]]") -> Settings:
    """
    Parse the command-line argument list into a Settings object.

    I'm rolling my own argument-parsing instead of using a library for maximum
    flexibility.
    """
    if argv is None:
        argv = sys.argv[1:]

    flags = {}
    posargs = []
    after_flags = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        longarg = short_to_long(arg)
        if longarg == "--":
            after_flags = True
        elif not after_flags and longarg in FLAGS:
            # --throttle and --init are the only flag that takes an argument.
            if longarg == "--throttle":
                if i == len(argv) - 1 or not argv[i + 1].isdigit():
                    sys.stderr.write("--throttle takes one integer argument.\n")
                    sys.exit(1)
                flags[longarg] = int(argv[i + 1])
                i += 1
            elif longarg == "--init":
                if i == len(argv) - 1:
                    sys.stderr.write("--init takes one argument.\n")
                    sys.exit(1)
                flags[longarg] = argv[i + 1]
                i += 1
            else:
                flags[longarg] = True
        # Special syntax for --init and --throttle.
        elif not after_flags and longarg.startswith("--throttle"):
            flags["--throttle"] = int(longarg[len("--throttle=") :])
        elif not after_flags and longarg.startswith("--init"):
            flags["--init"] = longarg[len("--init=") :]
        elif not after_flags and longarg.startswith("-") and len(longarg) > 1:
            sys.stderr.write("Unrecognized flag: " + arg + "\n")
            sys.exit(1)
        else:
            posargs.append(longarg)
        i += 1

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

    if "--credits" in flags:
        if len(flags) == 1 and not posargs:
            print(CREDITS)
            sys.exit(0)
        else:
            sys.stderr.write(
                "--credits may not be combined with other flags or commands.\n"
            )
            sys.exit(1)

    if len(posargs) == 0:
        sys.stderr.write("No file path supplied.\n")
        sys.exit(1)
    elif len(posargs) > 1:
        sys.stderr.write("Too many file paths supplied.\n")
        sys.exit(1)

    if "debug" in flags:
        mode = "debug"
    elif "assemble" in flags:
        mode = "assemble"
    elif "preprocess" in flags:
        mode = "preprocess"
    elif "disassemble" in flags:
        mode = "disassemble"
    else:
        mode = ""

    for picky_flag, valid_modes in PICKY_FLAGS.items():
        if picky_flag in flags:
            if mode not in valid_modes:
                sys.stderr.write(
                    "{} is not compatible with the chosen mode.\n".format(picky_flag)
                )
                sys.exit(1)

    if "--quiet" in flags and "--verbose" in flags:
        sys.stderr.write("--quiet and --verbose are incompatible.\n")
        sys.exit(1)

    for f in FLAGS:
        if f not in flags:
            flags[f] = False

    settings = Settings()
    settings.path = posargs[0]
    settings.mode = mode

    settings.allow_interrupts = settings.mode in ("assemble", "preprocess")
    settings.code = flags["--code"]
    settings.color = not flags["--no-color"]
    settings.data = flags["--data"]
    if flags["--big-stack"]:
        # Arbitrary value copied over from HERA-C.
        settings.data_start = 0xC167
    if flags["--init"] is False:
        settings.init = []
    else:
        settings.init = parse_init_string(flags["--init"])
        if settings.init is None:
            sys.stderr.write("Invalid syntax for --init argument.\n\n")
            sys.stderr.write('Sample correct syntax: --init="r1=5, r2=7"\n')
            sys.exit(1)
    settings.no_debug_ops = flags["--no-debug-ops"]
    settings.obfuscate = flags["--obfuscate"]
    settings.stdout = flags["--stdout"]
    settings.throttle = flags["--throttle"]
    settings.warn_octal_on = not flags["--warn-octal-off"]
    settings.warn_return_on = not flags["--warn-return-off"]
    if flags["--verbose"]:
        settings.volume = VOLUME_VERBOSE
    elif flags["--quiet"]:
        settings.volume = VOLUME_QUIET

    return settings


def short_to_long(arg: str) -> str:
    """Convert the short form of an argument to its long form."""
    if arg == "-h":
        return "--help"
    elif arg == "-v":
        return "--version"
    elif arg == "-q":
        return "--quiet"
    else:
        return arg


def parse_init_string(initstr: str) -> "Optional[List[Tuple[int, int]]]":
    """
    Parse the argument to --init into a list of (index, value) pairs.

    Return None if the string is ill-formatted.
    """
    initstr = initstr.replace(",", " ")
    assignments = initstr.split()
    ret = []
    for asgn in assignments:
        try:
            lhs, rhs = asgn.split("=", maxsplit=1)
        except ValueError:
            return None

        try:
            dest = register_to_index(lhs)
        except HERAError:
            return None

        try:
            val = int(rhs, base=0)
        except ValueError:
            return None

        ret.append((dest, val))

    return ret


def dump_state(vm: VirtualMachine, settings: Settings) -> None:
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


FLAGS = {
    "--big-stack",
    "--code",
    "--credits",
    "--data",
    "--help",
    "--init",
    "--no-color",
    "--no-debug-ops",
    "--obfuscate",
    "--quiet",
    "--stdout",
    "--throttle",
    "--verbose",
    "--version",
    "--warn-octal-off",
    "--warn-return-off",
    "assemble",
    "debug",
    "disassemble",
    "preprocess",
}

# Map from flag names to compatible modes, e.g. "--big-stack" is only compatible with
# the run, debug and assemble modes.
PICKY_FLAGS = {
    "--big-stack": ["", "debug", "assemble"],
    "--obfuscate": ["preprocess"],
    "--throttle": [""],
    "--warn-return-off": ["", "debug"],
    "--code": ["assemble"],
    "--data": ["assemble"],
    "--stdout": ["assemble"],
    "--init": ["", "debug"],
}

CREDITS = (
    VERSION
    + """

Developed by Ian Fisher (HC '19) - iafisher@protonmail.com."""
)
HELP = """\
hera: an interpreter for the Haverford Educational RISC Architecture.

Usage:
    hera <path>
    hera debug <path>
    hera assemble <path>
    hera preprocess <path>
    hera disassemble <path>

Common options:
    -h, --help         Show this message and exit.
    -v, --version      Show the version and exit.
    --credits          Print the credits for hera-py development.

    --no-color         Do not print colored output.
    --no-debug-ops     Disallow debugging instructions.
    -q, --quiet        Set output level to quiet.
    --verbose          Set output level to verbose.
    --warn-octal-off   Do not print warnings for zero-prefixed integer literals.

Interpreter and debugger options:
    --big-stack        Reserve more space for the stack.
    --init=<str>
    --init <str>       Initialize registers with the given expression,
                       e.g. "r1=5, r2=6"
    --throttle=<n>
    --throttle <n>     Exit after <n> instructions have been executed.
    --warn-return-off  Do not print warnings for invalid RETURN addresses.

Assembler options:
    --code             Only output the assembled code.
    --data             Only output the assembled data.
    --stdout           Print the assembled program to stdout instead of creating
                       files.
"""
