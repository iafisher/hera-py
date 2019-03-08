"""The shell interface to the HERA debugger.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: March 2019
"""
import copy
import functools
from typing import List, Optional

from . import miniparser
from .debugger import Debugger
from .miniparser import (
    InfixNode,
    IntNode,
    MemoryNode,
    PrefixNode,
    RegisterNode,
    SymbolNode,
)
from hera.assembler import assemble_and_print
from hera.data import DataLabel, HERAError, Label, Location, Program, Settings
from hera.disassembler import disassemble
from hera.loader import load_program
from hera.op import Branch, DataOperation, LABEL
from hera.parser import parse
from hera.utils import format_int, pad


def debug(program: Program, settings: Settings) -> None:
    """Start the debug loop."""
    debugger = Debugger(program, settings)
    Shell(debugger, settings).loop()


def mutates(handler):
    """Decorator for command handlers in the Shell class that mutate the state of the
    debugger.
    """

    @functools.wraps(handler)
    def inner(self, *args, **kwargs):
        self.debugger.save()
        name = handler.__name__[len("handle_") :]
        self.command_history.append(name)
        return handler(self, *args, **kwargs)

    return inner


class Shell:
    def __init__(self, debugger: Debugger, settings: Settings) -> None:
        self.debugger = debugger
        self.settings = settings
        self.command_history = []  # type: List[str]

    def loop(self):
        if self.debugger.empty():
            print("Cannot debug an empty program.")
            return

        self.print_current_op()

        while True:
            try:
                response = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not response:
                continue
            else:
                should_continue = self.handle_command(response)
                if should_continue is False:
                    break

    def handle_command(self, response: str) -> bool:
        """Parse the command and execute it. Return False if the loop should exit, and
        True otherwise.
        """
        try:
            cmd, argstr = response.split(maxsplit=1)
        except ValueError:
            cmd = response
            argstr = ""

        try:
            fullcmd = self.expand_command(cmd)
        except HERAError:
            if "=" in response:
                self.handle_assign(response.split("=", maxsplit=1))
            else:
                print("{} is not a recognized command.".format(cmd))

            return True
        else:
            if fullcmd == "quit":
                return False

            handler = getattr(self, "handle_" + fullcmd)
            if fullcmd in self.TAKES_ARGSTR:
                handler(argstr)
            else:
                handler(argstr.split())

            return True

    # Commands which may be abbreviated with a prefix. Order determines precedence when
    # multiple commands share a prefix.
    CAN_BE_ABBREVIATED = (
        # Multiple lists to prevent reformatting.
        ["assign", "break", "continue", "clear", "execute", "goto"]
        + ["help", "info", "list", "next", "print", "quit", "step", "undo"]
    )

    # Commands that require the whole command to be spelled out.
    CANNOT_BE_ABBREVIATED = ["asm", "dis", "ll", "off", "on", "restart"]

    # Commands that do not take a whitespace-separated list of argument.
    TAKES_ARGSTR = ["asm", "execute", "print"]

    def expand_command(self, cmd: str) -> str:
        cmd = cmd.lower()
        for full in self.CAN_BE_ABBREVIATED:
            if full.startswith(cmd):
                return full

        for full in self.CANNOT_BE_ABBREVIATED:
            if full == cmd:
                return full

        raise HERAError

    def handle_asm(self, argstr: str) -> None:
        if not argstr.strip():
            print("asm takes one argument.")
            return

        try:
            program = load_program(argstr, self.settings)
        except SystemExit:
            return

        settings = self.asm_settings()
        assemble_and_print(program, settings)

    @mutates
    def handle_assign(self, args: List[str]) -> None:
        if len(args) != 2:
            print("assign takes two arguments.")
            return

        try:
            ltree = miniparser.parse(args[0])
            rtree = miniparser.parse(args[1])
        except SyntaxError as e:
            msg = str(e)
            if msg:
                print("Parse error: " + msg + ".")
            else:
                print("Parse error.")
            return

        if len(ltree.seq) > 1:
            print("Parse error: cannot assign to sequence.")
            return

        if len(rtree.seq) > 1:
            print("Parse error: cannot assign sequence value.")
            return

        ltree = ltree.seq[0]
        rtree = rtree.seq[0]

        vm = self.debugger.vm
        try:
            rhs = self.evaluate_node(rtree)
            if isinstance(ltree, RegisterNode):
                vm.store_register(ltree.value, rhs)
            elif isinstance(ltree, MemoryNode):
                address = self.evaluate_node(ltree.address)
                vm.store_memory(address, rhs)
            elif isinstance(ltree, SymbolNode):
                if ltree.value == "pc":
                    vm.pc = rhs
                else:
                    print("Eval error: cannot assign to symbol.")
            elif isinstance(ltree, (InfixNode, PrefixNode)):
                print("Eval error: cannot assign to arithmetic expression.")
            else:
                raise RuntimeError(
                    "unknown node type {}".format(ltree.__class__.__name__)
                )
        except HERAError as e:
            print("Eval error: " + str(e) + ".")

    @mutates
    def handle_break(self, args: List[str]) -> None:
        if len(args) > 1:
            print("break takes zero or one arguments.")
            return

        if len(args) == 0:
            breakpoints = self.debugger.get_breakpoints()
            if breakpoints:
                for brk in breakpoints.values():
                    print(brk)
            else:
                print("No breakpoints set.")
        else:
            try:
                b = self.debugger.resolve_location(args[0])
            except ValueError as e:
                print("Error:", e)
            else:
                self.debugger.set_breakpoint(b)
                loc = self.debugger.op(b).loc
                print("Breakpoint set in file {0.path}, line {0.line}.".format(loc))

    @mutates
    def handle_clear(self, args: List[str]) -> None:
        if len(args) == 0:
            print("clear takes one or more arguments.")
            return

        if any(arg == "*" for arg in args):
            self.debugger.breakpoints.clear()
            print("Cleared all breakpoints.")
        else:
            for arg in args:
                try:
                    b = self.debugger.resolve_location(arg)
                except ValueError as e:
                    print("Error:", e)
                else:
                    if b in self.debugger.breakpoints:
                        loc = self.debugger.op(b).loc
                        del self.debugger.breakpoints[b]
                        msg = "Cleared breakpoint in file {0.path}, line {0.line}."
                        print(msg.format(loc))
                    else:
                        print("No breakpoint at that location.")

    @mutates
    def handle_continue(self, args: List[str]) -> None:
        if len(args) != 0:
            print("continue takes no arguments.")
            return

        self.debugger.next(step=True)
        while not self.debugger.finished() and not self.debugger.at_breakpoint():
            self.debugger.next(step=True)

        self.print_current_op()

    def handle_dis(self, args: List[str]) -> None:
        if len(args) != 1:
            print("dis takes one argument.")
            return

        try:
            v = int(args[0], base=0)
        except ValueError:
            print("Could not parse argument to dis.")
            return

        data = bytes([v >> 8, v & 0xFF])
        try:
            print(disassemble(data))
        except HERAError as e:
            print("Error:", e)

    @mutates
    def handle_execute(self, argstr: str) -> None:
        if not argstr.strip():
            print("execute takes one argument.")
            return

        # Make sure there are no disallowed ops.
        for op in parse(argstr)[0]:
            if isinstance(op, Branch):
                print("execute cannot take branching operations.")
                return
            elif isinstance(op, DataOperation):
                print("execute cannot take data statements.")
                return
            elif isinstance(op, LABEL):
                print("execute cannot take labels.")
                return

        try:
            program = load_program(argstr, self.settings)
        except SystemExit:
            return

        vm = self.debugger.vm
        opc = vm.pc
        for op in program.code:
            op.execute(vm)
        vm.pc = opc

    @mutates
    def handle_goto(self, args: List[str]) -> None:
        if len(args) != 1:
            print("goto takes one argument.")
            return

        try:
            new_pc = self.debugger.resolve_location(args[0])
        except ValueError as e:
            print("Error:", str(e))
            return
        else:
            self.debugger.vm.pc = new_pc

        self.print_current_op()

    def handle_help(self, args: List[str]) -> None:
        if not args:
            print(HELP)
        else:
            for i, arg in enumerate(args):
                try:
                    fullarg = self.expand_command(arg)
                except HERAError:
                    print("{} is not a recognized command.".format(arg))
                else:
                    print(HELP_MAP[fullarg])

                if i != len(args) - 1:
                    print()

    def handle_info(self, args: List[str]) -> None:
        if args:
            try:
                fullargs = [self.expand_info_arg(arg) for arg in args]
            except HERAError as e:
                print("Error: " + str(e) + ".")
                return
        else:
            fullargs = ["registers", "flags", "stack"]

        for i, fullarg in enumerate(fullargs):
            if fullarg == "stack":
                self.info_stack()
            elif fullarg == "symbols":
                self.info_symbols()
            elif fullarg == "registers":
                self.info_registers()
            elif fullarg == "flags":
                self.info_flags()
            else:
                raise RuntimeError("this should never happen!")

            if i != len(fullargs) - 1:
                print()

    def expand_info_arg(self, arg: str) -> str:
        arg = arg.lower()
        if "stack".startswith(arg):
            # "stack" comes before "symbols" because "s" should resolve to "stack".
            return "stack"
        elif "symbols".startswith(arg):
            return "symbols"
        elif "registers".startswith(arg):
            return "registers"
        elif "flags".startswith(arg):
            return "flags"
        else:
            raise HERAError("unrecognized argument `{}`".format(arg))

    def handle_list(self, args: List[str]) -> None:
        if len(args) > 1:
            print("list takes zero or one arguments.")
            return

        try:
            context = int(args[0], base=0) if args else 3
        except ValueError:
            print("Could not parse argument to list.")
            return

        if not self.debugger.finished():
            loc = self.debugger.op().loc
            self.print_range_of_ops(loc, context=context)
        else:
            print("Program has finished executing.")

    def handle_ll(self, args: List[str]) -> None:
        if len(args) != 0:
            print("ll takes no arguments.")
            return

        if not self.debugger.finished():
            loc = self.debugger.op().loc
            self.print_range_of_ops(loc)
        else:
            print("Program has finished executing.")

    @mutates
    def handle_next(self, args: List[str]) -> None:
        if len(args) > 1:
            print("next takes zero or one arguments.")
            return

        if not self.debugger.finished():
            try:
                n = int(args[0]) if args else 1
            except ValueError:
                print("Could not parse argument to next.")
                return

            for _ in range(n):
                if self.debugger.finished():
                    break
                self.debugger.next(step=False)

        self.print_current_op()

    @mutates
    def handle_off(self, args: List[str]) -> None:
        if len(args) == 0:
            print("off takes one or more arguments.")
            return

        try:
            flags = resolve_flags(args)
        except HERAError as e:
            print(e)
            return

        for flag in flags:
            setattr(self.debugger.vm, flag, False)

    @mutates
    def handle_on(self, args: List[str]) -> None:
        if len(args) == 0:
            print("on takes one or more arguments.")
            return

        try:
            flags = resolve_flags(args)
        except HERAError as e:
            print(e)
            return

        for flag in flags:
            setattr(self.debugger.vm, flag, True)

    def handle_print(self, argstr: str) -> None:
        if not argstr:
            print("print takes one or more arguments.")
            return

        try:
            tree = miniparser.parse(argstr)
        except SyntaxError as e:
            msg = str(e)
            if msg:
                print("Parse error: {}.".format(msg))
            else:
                print("Parse error.".format(msg))
        else:
            spec = tree.fmt
            for c in spec:
                if c not in "dxobcsl":
                    print("Unknown format specifier `{}`.".format(c))
                    return

                # 'c' and 's' do not always generate output, if the given value is not a
                # char or signed integer, respectively. Output can be forced with the
                # 'C' and 'S', which we do if the user explicitly provided these
                # formats.
                spec = spec.replace("c", "C")
                spec = spec.replace("s", "S")

            try:
                if len(tree.seq) > 1:
                    for arg in tree.seq:
                        self.print_one_expr(arg, spec, with_lhs=True)
                else:
                    self.print_one_expr(tree.seq[0], spec)
            except HERAError as e:
                print("Eval error: {}.".format(e))

    def print_one_expr(self, tree, spec: str, *, with_lhs=False) -> None:
        """Print a single expression with the given format specification."""

        # Customize the format specifier depending on the type of expression.
        if isinstance(tree, RegisterNode):
            # R13 is used to hold the return value of the PC in function calls,
            # so printing the location is useful.
            if tree.value == 13 and not spec:
                spec = augment_spec(spec, "l")
        elif isinstance(tree, SymbolNode):
            if tree.value.lower() == "pc":
                spec = augment_spec(spec, "l")
            else:
                try:
                    value = self.debugger.symbol_table[tree.value]
                except KeyError:
                    raise HERAError("{} is not defined".format(tree.value))
                else:
                    if isinstance(value, Label):
                        spec = augment_spec(spec, "l")
        elif isinstance(tree, IntNode):
            if not spec:
                spec = "d"

        value = self.evaluate_node(tree)
        if with_lhs:
            print("{} = {}".format(tree, self.format_int(value, spec)))
        else:
            print(self.format_int(value, spec))

    @mutates
    def handle_restart(self, args: List[str]) -> None:
        if len(args) != 0:
            print("restart takes no arguments.")
            return

        self.debugger.reset()
        self.print_current_op()

    @mutates
    def handle_step(self, args: List[str]) -> None:
        if len(args) > 0:
            print("step takes no arguments.")
            return

        if self.debugger.op().name != "CALL":
            print("step is only valid when the current instruction is CALL.")
            return

        self.debugger.next(step=True)
        self.print_current_op()

    def handle_undo(self, args: List[str]) -> None:
        if len(args) > 0:
            print("undo takes no arguments.")
            return

        if self.debugger.old is None:
            print("Nothing to undo.")
            return
        else:
            print("Undid {}.".format(self.command_history.pop()))

        self.debugger = self.debugger.old

    def info_registers(self) -> None:
        nonzero = 0
        for i, r in enumerate(self.debugger.vm.registers[1:], start=1):
            if r != 0:
                nonzero += 1
                end = ", " if i != 15 or nonzero < 15 else ""
                print("R{} = {}".format(i, r), end=end)

        if nonzero == 0:
            print("All registers set to zero.")
        elif nonzero != 15:
            print("all other registers set to zero.")
        else:
            print()

    def info_flags(self) -> None:
        vm = self.debugger.vm
        flags = []
        if vm.flag_carry_block:
            flags.append("carry-block flag is on")
        if vm.flag_carry:
            flags.append("carry flag is on")
        if vm.flag_overflow:
            flags.append("overflow flag is on")
        if vm.flag_zero:
            flags.append("zero flag is on")
        if vm.flag_sign:
            flags.append("sign flag is on")

        if len(flags) == 5:
            print("All flags are on.")
        elif len(flags) == 0:
            print("All flags are off.")
        else:
            flagstr = ", ".join(flags)
            flagstr = flagstr[0].upper() + flagstr[1:]
            print(flagstr + ", all other flags are off.")

    def info_stack(self) -> None:
        vm = self.debugger.vm
        if vm.expected_returns:
            print("Call stack (last call at bottom)")
            for call_address, return_address in vm.expected_returns:
                fname = self.debugger.find_label(call_address)
                floc = self.debugger.get_breakpoint_name(
                    call_address, append_label=False
                )
                rloc = self.debugger.get_breakpoint_name(
                    return_address - 1, append_label=False
                )
                if fname is not None:
                    print("  {} ({}, called from {})".format(fname, floc, rloc))
                else:
                    print("  {} (called from {})".format(floc, rloc))
        else:
            print("The call stack is empty.")

    def info_symbols(self) -> None:
        constants = []
        labels = []
        dlabels = []
        for key, val in self.debugger.symbol_table.items():
            if isinstance(val, Label):
                debug_info = self.debugger.program.debug_info
                labels.append("{} ({})".format(key, debug_info.labels[key]))
            elif isinstance(val, DataLabel):
                dlabels.append("{} (0x{:x})".format(key, val))
            else:
                constants.append("{} ({})".format(key, val))

        if constants:
            print("Constants: " + ", ".join(constants))

        if labels:
            print("Labels: " + ", ".join(labels))

        if dlabels:
            print("Data labels: " + ", ".join(dlabels))

    def evaluate_node(self, node) -> int:
        vm = self.debugger.vm
        if isinstance(node, IntNode):
            if node.value >= 2 ** 16 or node.value < -2 ** 15:
                raise HERAError("integer literal exceeds 16 bits")
            return node.value
        elif isinstance(node, RegisterNode):
            return vm.load_register(node.value)
        elif isinstance(node, MemoryNode):
            address = self.evaluate_node(node.address)
            return vm.load_memory(address)
        elif isinstance(node, SymbolNode):
            if node.value.lower() == "pc":
                return vm.pc
            else:
                try:
                    return self.debugger.symbol_table[node.value]
                except KeyError:
                    raise HERAError("{} is not defined".format(node.value))
        elif isinstance(node, PrefixNode):
            arg = self.evaluate_node(node.arg)
            if node.op == "-":
                result = -arg
            else:
                raise RuntimeError("unhandled prefix operator: " + node.op)

            if overflow(result):
                raise HERAError("overflow from unary " + node.op)

            return result
        elif isinstance(node, InfixNode):
            left = self.evaluate_node(node.left)
            right = self.evaluate_node(node.right)
            if node.op == "+":
                result = left + right
            elif node.op == "-":
                result = left - right
            elif node.op == "*":
                result = left * right
            elif node.op == "/":
                if right == 0:
                    raise HERAError("division by zero")
                result = left // right
            else:
                raise RuntimeError("unhandled infix operator: " + node.op)

            if overflow(result):
                raise HERAError("overflow from " + node.op)

            return result
        else:
            raise RuntimeError("unknown node type {}".format(node.__class__.__name__))

    def print_current_op(self) -> None:
        """Print the next operation to be executed. If the program has finished
        executed, nothing is printed.
        """
        if not self.debugger.finished():
            loc = self.debugger.op().loc
            self.print_range_of_ops(loc, context=1)
        else:
            print("Program has finished executing.")

    def print_range_of_ops(self, loc: Location, context: Optional[int] = None) -> None:
        """Print the line indicated by `loc`, as well as `context` previous and
        following lines. If `context` is None, the whole file is printed.
        """
        lineno = loc.line - 1
        lines = loc.file_lines
        max_lineno_width = len(str(len(lines)))

        if context is None:
            lo = 0
            hi = len(lines)
        else:
            lo = max(lineno - context, 0)
            hi = min(lineno + context + 1, len(lines))

        print("[{}]\n".format(loc.path))
        for i in range(lo, hi):
            prefix = "->  " if i == lineno else "    "
            print(prefix, end="")
            print(pad(str(i + 1), max_lineno_width), end="")

            line = lines[i].rstrip()
            if line:
                print("  " + line)
            else:
                print()

    def format_int(self, v: int, spec: str) -> str:
        if not spec:
            spec = DEFAULT_SPEC

        if "l" in spec:
            spec = spec.replace("l", "")
            loc = True
        else:
            loc = False

        if loc:
            try:
                label = self.debugger.get_breakpoint_name(v, append_label=False)
            except IndexError:
                return format_int(v, spec=spec)
            else:
                return format_int(v, spec=spec) + " [" + label + "]"
        else:
            return format_int(v, spec=spec)

    def asm_settings(self):
        """Override some defaults in self.settings for the assembler."""
        settings = copy.copy(self.settings)
        settings.stdout = True
        settings.code = True
        settings.data = False
        return settings


DEFAULT_SPEC = "dsc"


def augment_spec(spec: str, f: str) -> str:
    """Augment the format specifier with the additional format character."""
    if not spec:
        return augment_spec(DEFAULT_SPEC, f)
    else:
        return spec + f if f not in spec else spec


FLAG_SHORT_TO_LONG = {
    "cb": "carry_block",
    "c": "carry",
    "v": "overflow",
    "s": "sign",
    "z": "zero",
}


def resolve_flags(args: List[str]) -> List[str]:
    flags = []
    for arg in args:
        arg = arg.replace("-", "_")
        if arg not in FLAG_SHORT_TO_LONG.values():
            try:
                longflag = FLAG_SHORT_TO_LONG[arg]
            except KeyError:
                raise HERAError("Unrecognized flag: `{}`.".format(arg))
            else:
                flags.append("flag_" + longflag)
        else:
            flags.append("flag_" + arg)
    return flags


def overflow(v: int) -> bool:
    return v >= 2 ** 16 or v < -2 ** 15


HELP = """\
Available commands:
    asm <op>        Show the binary machine code that the HERA operations
                    assembles to.

    assign <x> <y>  Assign the value of y to x.

    break <loc>     Set a breakpoint at the given location. When no arguments
                    are given, all current breakpoints are printed.

    clear <loc>     Clear a breakpoint at the given location.

    continue        Execute the program until a breakpoint is encountered or
                    the program terminates.

    dis <n>         Disassemble the 16-bit integer into a HERA operation.

    execute <op>    Execute a HERA operation.

    goto <loc>      Jump to the given location.

    help            Print this help message.

    info            Print information about the current state of the program.

    list <n>        Print the current lines of source code and the n previous
                    and next lines. If not provided, n defaults to 3.

    ll              Print the entire program.

    next            Execute the current line.

    off <flag>      Turn the given machine flag off.

    on <flag>       Turn the given machine flag on.

    print <x>       Print the value of x.

    restart         Restart the execution of the program from the beginning.

    step            Step into the execution of a function.

    undo            Undo the last operation.

    quit            Exit the debugger.

    <x> = <y>       Alias for "assign <x> <y>".

Command names can generally be abbreviated with a unique prefix, e.g. "n" for
"next".
"""


HELP_MAP = {
    # asm
    "asm": """\
asm <op>
  Assemble the HERA operation into machine code.""",
    # assign
    "assign": """\
assign <x> <y>
  Assign the value of y to x. x may be a register, a memory location, or the
  program counter. y may be a register, a memory location, the program counter,
  a symbol, or an integer.

<x> = <y>
  Alias for "assign <x> <y>", with the additional advantage that <x> and <y>
  may contain spaces.

  Examples:
    Assign to a register:          R1 = 42
    Assign to a memory location:   @(1000) = R4
    Assign a label to a register:  R1 = some_label
    Arithmetic:                    R7 = R5 * 10""",
    # break
    "break": """\
break
  Print all current breakpoints.

break <n>
  Set a breakpoint at the given line number in the file that the debugger was
  opened on.

break <path>:<n>
  Set a breakpoint at the given line number in the given file.

break <label>
  Set a breakpoint at the given label.
  
break .
  Set a breakpoint at the current instruction.""",
    # clear
    "clear": """\
clear <location>
  Clear a breakpoint at the given line. Location formats accepted are the same
  as the break command.

clear *
  Clear all breakpoints.""",
    # continue
    "continue": """\
continue
  Execute the program until a breakpoint is encountered or the program
  terminates.""",
    # dis
    "dis": """\
dis <n>
   Interpret the 16-bit integer as a HERA machine instruction, and disassemble
   it into its assembly-language mnemonic.""",
    # execute
    "execute": """\
execute <op>
  Execute a HERA operation. The operation must not be a data statement or a
  branch. The operation may affect registers and memory. Some operations can
  be more concisely expressed with the debugging mini-language. Type
  "help assign" for details.

  Examples:
    execute ASR(R5, R4)""",
    # goto
    "goto": """\
goto <loc>
  Jump to the given location (either a line number or a label) without
  executing any of the intermediate instructions.""",
    # help
    "help": """\
help
  Print a summary of all debugging commands.

help <cmd>...
  Print a detailed help message for each command list.""",
    # info
    "info": """\
info <arg>...
  Print information about the current state of the program. Valid arguments to
  info are "registers", "stack", "flags" and "symbols". Arguments may be
  abbreviated with a unique prefix. The argument list defaults to "registers",
  "flags", and "stack" if not provided.""",
    # list
    "list": """\
list
  Print the current line of source and the three previous and next lines.

list <n>
  Print the current line of source code and the `n` previous and next lines.""",
    # ll
    "ll": """\
ll
  Print every line of the current file's source code.""",
    # next
    "next": """\
next
  Execute the current line. If the current line is a CALL instruction, the
  debugger executes the entire function (including nested and recursive calls)
  and moves on to the next line. If you wish to neter over the function call,
  use `step` instead.

next <n>
  Execute the next n instructions. This command will follow branches, so be
  careful!""",
    # off
    "off": """\
off <f1> <f2>...
    Turn off all the HERA machine flags listed. Flags may be given in long
    form (carry-block, carry, overflow, sign, zero) or short form (cb, c, v,
    s, z).""",
    # on
    "on": """\
on <f1> <f2>...
    Turn on all the HERA machine flags listed. Flags may be given in long form
    (carry-block, carry, overflow, sign, zero) or short form (cb, c, v, s, z).""",
    # print
    "print": """\
print <x> <y> <z>...
  Print the values of all the supplied arguments. The first argument may
  optionally be a format specifier, e.g. ":xds". Each character of the string
  identifies a format in which to print the value. The following formats are
  recognized: d for decimal, x for hexadecimal, o for octal, b for binary, c
  for character literals, s for signed integers, and l for source code
  locations. When not provided, the format specifier defaults to ":xdsc".

  Examples:
    A register:        print R7
    A memory location: print @1000
    A symbol:          print some_label
    Multiple values:   print R1, R2, R3
    Formatted:         print :bl PC_ret
    Arithmetic:        print @(@(FP+1)) * 7""",
    # restart
    "restart": """\
restart
  Restart execution of the program from the beginning. All registers and
  memory cells are reset.""",
    # step
    "step": """\
step
  Step into the execution of a function.  The step command is only valid when
  the current instruction is CALL.""",
    # undo
    "undo": """\
undo
  Undo the last operation that changed the state of the debugger.""",
    # quit
    "quit": """\
quit
  Exit the debugger.""",
}
