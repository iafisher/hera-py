import functools
from typing import List

from . import minilanguage
from .debugger import Debugger
from .minilanguage import (
    AddNode,
    DivNode,
    IntNode,
    MemoryNode,
    MinusNode,
    MulNode,
    RegisterNode,
    SubNode,
    SymbolNode,
)
from hera.data import DataLabel, HERAError, Label, Program, Settings
from hera.loader import load_program
from hera.parser import parse
from hera.utils import BRANCHES, DATA_STATEMENTS, format_int, pad, register_to_index


def debug(program: Program, settings=Settings()) -> None:
    """Start the debug loop."""
    debugger = Debugger(program)
    Shell(debugger, settings).loop()


def mutates(f):
    """Decorator for command handlers in the Shell class that mutate the state of the
    debugger."""

    @functools.wraps(f)
    def inner(self, *args, **kwargs):
        self.debugger.save()
        return f(self, *args, **kwargs)

    return inner


class Shell:
    def __init__(self, debugger, settings=Settings()):
        self.debugger = debugger
        self.settings = settings

    def loop(self):
        if not self.debugger.program:
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
            elif "quit".startswith(response.lower()):
                break
            else:
                self.handle_command(response)

    def handle_command(self, response):
        """Parse the command and execute it. Return False if the loop should exit, and
        True otherwise.
        """
        try:
            cmd, argstr = response.split(maxsplit=1)
        except ValueError:
            cmd = response
            argstr = ""

        arglist = argstr.split()
        cmd = cmd.lower()
        if "assign".startswith(cmd):
            self.handle_assign(arglist)
        elif "break".startswith(cmd):
            self.handle_break(arglist)
        elif "continue".startswith(cmd):
            self.handle_continue(arglist)
        elif "execute".startswith(cmd):
            self.handle_execute(argstr)
        elif "help".startswith(cmd):
            self.handle_help(arglist)
        elif "info".startswith(cmd):
            self.handle_info(arglist)
        elif "jump".startswith(cmd):
            self.handle_jump(arglist)
        elif "list".startswith(cmd):
            self.handle_list(arglist)
        elif cmd == "ll":
            self.handle_ll(arglist)
        elif "next".startswith(cmd):
            self.handle_next(arglist)
        elif cmd == "off":
            self.handle_off(arglist)
        elif cmd == "on":
            self.handle_on(arglist)
        elif "print".startswith(cmd):
            self.handle_print(argstr)
        # restart cannot be abbreviated, so that users don't accidentally restart.
        elif cmd == "restart":
            self.handle_restart(arglist)
        elif "step".startswith(cmd):
            self.handle_step(arglist)
        elif "undo".startswith(cmd):
            self.handle_undo(arglist)
        elif "=" in response:
            self.handle_assign(response.split("=", maxsplit=1))
        else:
            print("{} is not a recognized command.".format(cmd))

    def handle_assign(self, args):
        if len(args) != 2:
            print("assign takes two arguments.")
            return

        try:
            ltree = minilanguage.parse(args[0])
            rtree = minilanguage.parse(args[1])
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
                if ltree.value == "pc":
                    vm.pc = rhs
                else:
                    vm.store_register(ltree.value, rhs)
            elif isinstance(ltree, MemoryNode):
                address = self.evaluate_node(ltree.address)
                vm.assign_memory(address, rhs)
            elif isinstance(ltree, SymbolNode):
                print("Eval error: cannot assign to symbol.")
            elif isinstance(ltree, (AddNode, SubNode, DivNode, MulNode, MinusNode)):
                print("Eval error: cannot assign to arithmetic expression.")
            else:
                raise RuntimeError(
                    "unknown node type {}".format(ltree.__class__.__name__)
                )
        except HERAError as e:
            print("Eval error: " + str(e) + ".")

    @mutates
    def handle_break(self, args):
        if len(args) > 1:
            print("break takes zero or one arguments.")
            return

        # TODO: In pdb, break with no arguments set a breakpoint at the current
        # line. Should I do that too?
        #
        # Better idea: accept "." as a location for the current line.
        if len(args) == 0:
            breakpoints = self.debugger.get_breakpoints()
            if breakpoints:
                for b in breakpoints.values():
                    print(b)
            else:
                print("No breakpoints set.")
        else:
            try:
                b = self.debugger.resolve_location(args[0])
            except ValueError as e:
                print("Error:", e)
            else:
                self.debugger.set_breakpoint(b)

    @mutates
    def handle_continue(self, args):
        if len(args) != 0:
            print("continue takes no arguments.")
            return

        self.debugger.exec_ops(until=lambda dbg: dbg.vm.pc in dbg.breakpoints)
        self.print_current_op()

    @mutates
    def handle_execute(self, argstr):
        # Make sure there are no disallowed ops.
        for op in parse(argstr)[0]:
            if op.name in BRANCHES or op.name in ("CALL", "RETURN"):
                print("execute cannot take branching operations.")
                return
            elif op.name in DATA_STATEMENTS:
                print("execute cannot take data statements.")
                return
            elif op.name == "LABEL":
                print("execute cannot take labels.")
                return

        try:
            program = load_program(argstr, self.settings)
        except SystemExit:
            return

        vm = self.debugger.vm
        opc = vm.pc
        for op in program.code:
            vm.exec_one(op)
        vm.pc = opc

    def handle_help(self, args):
        if not args:
            print(HELP)
        else:
            for i, arg in enumerate(args):
                try:
                    print(HELP_MAP[arg])
                except KeyError:
                    print("{} is not a recognized command.".format(arg))

                if i != len(args) - 1:
                    print()

    def handle_info(self, args):
        if len(args) != 0:
            print("info takes no arguments.")
            return

        self.print_registers()
        self.print_flags()
        print()

        constants = []
        labels = []
        dlabels = []
        for key, val in self.debugger.symbol_table.items():
            if isinstance(val, Label):
                lineno = self.debugger.get_breakpoint_name(val, append_label=False)
                labels.append("{} ({})".format(key, lineno))
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

    @mutates
    def handle_jump(self, args):
        if len(args) > 1:
            print("jump takes zero or one arguments.")
            return

        if len(args) == 1:
            try:
                new_pc = self.debugger.resolve_location(args[0])
            except ValueError as e:
                print("Error:", str(e))
                return
            else:
                self.debugger.vm.pc = new_pc
        else:
            self.debugger.vm.pc += len(self.debugger.get_real_ops())

        self.print_current_op()

    def handle_list(self, args):
        if len(args) > 1:
            print("list takes zero or one arguments.")
            return

        try:
            context = int(args[0], base=0) if args else 3
        except ValueError:
            print("Could not parse argument to list.")
            return

        loc = self.debugger.program[self.debugger.vm.pc].loc
        self.print_range_of_ops(loc, context=context)

    def handle_ll(self, args):
        if len(args) != 0:
            print("ll takes no arguments.")
            return

        loc = self.debugger.program[self.debugger.vm.pc].loc
        self.print_range_of_ops(loc)

    @mutates
    def handle_next(self, args):
        if len(args) > 1:
            print("next takes zero or one arguments.")
            return

        if self.debugger.is_finished():
            print("Program has finished executing. Enter 'r' to restart.")
            return

        try:
            n = int(args[0]) if args else 1
        except ValueError:
            print("Could not parse argument to next.")
            return

        self.debugger.exec_ops(n)
        self.print_current_op()

    @mutates
    def handle_off(self, args):
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
    def handle_on(self, args):
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

    def handle_print(self, argstr):
        if not argstr:
            print("print takes one or more arguments.")
            return

        try:
            tree = minilanguage.parse(argstr)
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

    def print_one_expr(self, tree, spec, *, with_lhs=False):
        """Print a single expression with the given format specification."""

        # Customize the format specifier depending on the type of expression.
        if isinstance(tree, RegisterNode):
            if tree.value.lower() == "pc":
                spec = augment_spec(spec, "l")
            else:
                try:
                    i = register_to_index(tree.value)
                except ValueError:
                    raise HERAError("no such register")
                else:
                    # R13 is used to hold the return value of the PC in function calls,
                    # so printing the location is useful.
                    if i == 13 and not spec:
                        spec = augment_spec(spec, "l")
        elif isinstance(tree, SymbolNode):
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
    def handle_restart(self, args):
        if len(args) != 0:
            print("restart takes no arguments.")
            return

        self.debugger.reset()
        self.print_current_op()

    @mutates
    def handle_step(self, args):
        if len(args) > 0:
            print("step takes no arguments.")
            return

        if self.debugger.program[self.debugger.vm.pc].original.name != "CALL":
            print("step is only valid when the current instruction is CALL.")
            return

        calls = self.debugger.calls
        self.debugger.exec_ops(until=lambda dbg: dbg.calls == calls)
        self.print_current_op()

    def handle_undo(self, args):
        if len(args) > 0:
            print("undo takes no arguments.")
            return

        if self.debugger.old is None:
            print("Nothing to undo.")
            return

        self.debugger = self.debugger.old

    def print_registers(self):
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

    def print_flags(self):
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

    def evaluate_node(self, node):
        vm = self.debugger.vm
        if isinstance(node, IntNode):
            if node.value >= 2 ** 16:
                raise HERAError("integer literal exceeds 16 bits")
            return node.value
        elif isinstance(node, RegisterNode):
            if node.value.lower() == "pc":
                return vm.pc
            else:
                return vm.get_register(node.value)
        elif isinstance(node, MemoryNode):
            address = self.evaluate_node(node.address)
            return vm.access_memory(address)
        elif isinstance(node, SymbolNode):
            try:
                return self.debugger.symbol_table[node.value]
            except KeyError:
                raise HERAError("{} is not defined".format(node.value))
        elif isinstance(node, MinusNode):
            return check_overflow(-self.evaluate_node(node.arg), "negation")
        elif isinstance(node, AddNode):
            left = self.evaluate_node(node.left)
            right = self.evaluate_node(node.right)
            return check_overflow(left + right, "addition")
        elif isinstance(node, SubNode):
            left = self.evaluate_node(node.left)
            right = self.evaluate_node(node.right)
            return check_overflow(left - right, "subtraction")
        elif isinstance(node, MulNode):
            left = self.evaluate_node(node.left)
            right = self.evaluate_node(node.right)
            return check_overflow(left * right, "multiplication")
        elif isinstance(node, DivNode):
            left = self.evaluate_node(node.left)
            right = self.evaluate_node(node.right)
            if right == 0:
                raise HERAError("division by zero")
            return check_overflow(left // right, "division")
        else:
            raise RuntimeError("unknown node type {}".format(node.__class__.__name__))

    def print_current_op(self):
        """Print the next operation to be executed. If the program has finished
        executed, nothing is printed.
        """
        if not self.debugger.is_finished():
            loc = self.debugger.program[self.debugger.vm.pc].loc
            self.print_range_of_ops(loc, context=1)
        else:
            print("Program has finished executing.")

    def print_range_of_ops(self, loc, context=None):
        """Print the line indicated by the Location object `loc`, as well as `context`
        previous and following lines. If `context` is None, the whole file is printed.
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

    def format_int(self, v, spec):
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


DEFAULT_SPEC = "dsc"


def augment_spec(spec, f):
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


def check_overflow(v: int, operation: str) -> int:
    if v >= 2 ** 16 or v < -2 ** 15:
        raise HERAError(operation + " overflow")
    else:
        return v


HELP = """\
Available commands:
    assign <x> <y>  Assign the value of y to x.

    break <loc>     Set a breakpoint at the given location. When no arguments
                    are given, all current breakpoints are printed.

    continue        Execute the program until a breakpoint is encountered or
                    the program terminates.

    execute <op>    Execute a HERA operation.

    help            Print this help message.

    info            Print information about the current state of the program.

    jump <loc>      Jump to the given location.

    list <n>        Print the current lines of source code and the n previous
                    and next lines. If not provided, n defaults to 3.

    ll              Print the entire program.

    next            Execute the current line.

    off <flag>      Turn the given machine flag off.

    on <flag>       Turn the given machine flag on.

    print <x>       Print the value of x.

    restart         Restart the execution of the program from the beginning.

    step            Step over the execution of a function.

    undo            Undo the last operation.

    quit            Exit the debugger.

    <x> = <y>       Alias for "assign <x> <y>".

Command names can generally be abbreviated with a unique prefix, e.g. "n" for
"next".
"""


HELP_MAP = {
    # assign
    "assign": """\
assign <x> <y>:
  Assign the value of y to x. x may be a register, a memory location, or the
  program counter. y may be a register, a memory location, the program counter,
  a symbol, or an integer.

<x> = <y>:
  Alias for "assign <x> <y>", with the additional advantage that <x> and <y>
  may contain spaces.

  Examples:
    Assign to a register:          R1 = 42
    Assign to a memory location:   @(1000) = R4
    Assign a label to a register:  R1 = some_label
    Arithmetic:                    R7 = R5 * 10""",
    # break
    "break": """\
break:
  Print all current breakpoints.

break <loc>:
  Set a breakpoint at the given location. The location may be a line number or
  a label.""",
    # continue
    "continue": """\
continue:
  Execute the program until a breakpoint is encountered or the program
  terminates.""",
    # execute
    "execute": """\
execute <op>:
  Execute a HERA operation. The operation must not be a data statement or a
  branch. The operation may affect registers and memory. Some operations can
  be more concisely expressed with the debugging mini-language. Type
  "help assign" for details.

  Examples:
    execute ASR(R5, R4)""",
    # help
    "help": """\
help:
  Print a summary of all debugging commands.

help <cmd>...:
  Print a detailed help message for each command list.""",
    # info
    "info": """\
info:
  Print information about the current state of the program.""",
    # jump
    "jump": """\
jump:
  Skip the current instruction.

jump <loc>:
  Jump to the given location (either a line number or a label) without
  executing any of the intermediate instructions.""",
    # list
    "list": """\
list:
  Print the current line of source and the three previous and next lines.

list <n>:
  Print the current line of source code and the `n` previous and next lines.""",
    # ll
    "ll": """\
ll:
  Print every line of the program's source code.""",
    # next
    "next": """\
next:
  Execute the current line. If the current line is a CALL instruction, the
  debugger enters the function being called. If you wish to skip over the
  function call, use `step` instead.

next <n>:
  Execute the next n instructions. This command will follow branches, so be
  careful!""",
    # off
    "off": """\
off <f1> <f2>...:
    Turn off all the HERA machine flags listed. Flags may be given in long
    form (carry-block, carry, overflow, sign, zero) or short form (cb, c, v,
    s, z).""",
    # on
    "on": """\
on <f1> <f2>...:
    Turn on all the HERA machine flags listed. Flags may be given in long form
    (carry-block, carry, overflow, sign, zero) or short form (cb, c, v, s, z).""",
    # print
    "print": """\
print <x> <y> <z>...:
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
restart:
  Restart execution of the program from the beginning. All registers and
  memory cells are reset.""",
    # step
    "step": """\
step:
  Step over the execution of a function. The step command is only valid when
  the current instruction is CALL. Stepping may behave unexpectedly in HERA
  programs that do not follow conventional function call idioms.""",
    # undo
    "undo": """\
undo:
  Undo the last operation that changed the state of the debugger.""",
    # quit
    "quit": """\
quit:
  Exit the debugger.""",
}
