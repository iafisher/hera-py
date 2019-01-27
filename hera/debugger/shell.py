from typing import Dict, List

from . import minilanguage
from .debugger import Debugger
from .minilanguage import (
    BoolNode,
    FLAG_LITERALS,
    IntNode,
    MemoryNode,
    RegisterNode,
    SymbolNode,
)
from hera.data import Constant, DataLabel, HERAError, Label, Op, Program, State
from hera.loader import load_program
from hera.parser import parse
from hera.utils import (
    BRANCHES,
    DATA_STATEMENTS,
    op_to_string,
    pad,
    print_register_debug,
)


def debug(program: Program) -> None:
    """Start the debug loop."""
    debugger = Debugger(program)
    Shell(debugger).loop()


class Shell:
    def __init__(self, debugger):
        self.debugger = debugger

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
        if "break".startswith(cmd):
            self.handle_break(arglist)
        elif "continue".startswith(cmd):
            self.handle_continue(arglist)
        elif "execute".startswith(cmd):
            self.handle_execute(argstr)
        elif "info".startswith(cmd):
            self.handle_info(arglist)
        elif "list".startswith(cmd):
            self.handle_list(arglist)
        elif cmd == "ll":
            self.handle_ll(arglist)
        elif "next".startswith(cmd):
            self.handle_next(arglist)
        elif "print".startswith(cmd):
            self.handle_print(argstr)
        elif "restart".startswith(cmd):
            self.handle_restart(arglist)
        elif cmd == "s":
            print("s is ambiguous between skip and step.")
        elif "skip".startswith(cmd):
            self.handle_skip(arglist)
        elif "step".startswith(cmd):
            self.handle_step(arglist)
        elif "help".startswith(cmd):
            self.handle_help(arglist)
        elif "=" in response:
            self.handle_assign(response.split("=", maxsplit=1))
        else:
            print("{} is not a recognized command.".format(cmd))

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

    def handle_continue(self, args):
        if len(args) != 0:
            print("continue takes no arguments.")
            return

        self.debugger.exec_ops(until=lambda dbg: dbg.vm.pc in dbg.breakpoints)
        self.print_current_op()

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
            program = load_program(argstr, State())
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
                dlabels.append("{} ({})".format(key, val))
            else:
                constants.append("{} ({})".format(key, val))

        if constants:
            print("Constants: " + ", ".join(constants))

        if labels:
            print("Labels: " + ", ".join(labels))

        if dlabels:
            print("Data labels: " + ", ".join(dlabels))

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

    def handle_next(self, args):
        if len(args) != 0:
            print("next takes no arguments.")
            return

        if self.debugger.is_finished():
            print("Program has finished executing. Enter 'r' to restart.")
            return

        self.debugger.exec_ops(1)
        self.print_current_op()

    def handle_print(self, argstr):
        try:
            tree = minilanguage.parse(argstr)
        except SyntaxError as e:
            msg = str(e)
            if msg:
                print("Parse error: " + msg + ".")
            else:
                print("Parse error.")
            return

        vm = self.debugger.vm
        try:
            if isinstance(tree, RegisterNode):
                if tree.value == "pc":
                    print("PC = {}".format(vm.pc))
                else:
                    value = vm.get_register(tree.value)
                    print_register_debug(tree.value, value, to_stderr=False)
            elif isinstance(tree, MemoryNode):
                address = self.evaluate_node(tree.address)
                print("M[{}] = {}".format(address, vm.access_memory(address)))
            elif isinstance(tree, SymbolNode):
                if tree.value in FLAG_LITERALS:
                    if tree.value == "f_cb":
                        print("Carry-block flag = " + str(vm.flag_carry_block).lower())
                    elif tree.value == "f_c":
                        print("Carry flag = " + str(vm.flag_carry).lower())
                    elif tree.value == "f_v":
                        print("Overflow flag = " + str(vm.flag_overflow).lower())
                    elif tree.value == "f_z":
                        print("Zero flag = " + str(vm.flag_zero).lower())
                    elif tree.value == "f_s":
                        print("Sign flag = " + str(vm.flag_sign).lower())
                    else:
                        raise RuntimeError("this should never happen!")

                    # If the symbol also happens to identify something in the symbol
                    # table (as well as a flag), print that too.
                    if tree.value in self.debugger.symbol_table:
                        self.print_symbol(
                            tree.value, self.debugger.symbol_table[tree.value]
                        )
                else:
                    try:
                        v = self.debugger.symbol_table[tree.value]
                    except KeyError:
                        print("{} is not defined.".format(tree.value))
                    else:
                        self.print_symbol(tree.value, v)
            elif isinstance(tree, IntNode):
                print(tree.value)
            else:
                raise RuntimeError(
                    "unknown node type {}".format(tree.__class__.__name__)
                )
        except HERAError as e:
            print("Eval error: " + str(e) + ".")

    def handle_restart(self, args):
        if len(args) != 0:
            print("restart takes no arguments.")
            return

        self.debugger.reset()
        self.print_current_op()

    def handle_skip(self, args):
        if len(args) > 1:
            print("skip takes zero or one arguments.")
            return

        if len(args) == 1:
            if args[0].startswith("+"):
                try:
                    offset = int(args[0][1:])
                except ValueError:
                    print("Could not parse argument to skip.")
                else:
                    for _ in range(offset):
                        self.debugger.vm.pc += len(self.debugger.get_real_ops())
            else:
                try:
                    new_pc = self.debugger.resolve_location(args[0])
                except ValueError as e:
                    print("Error:", str(e))
                else:
                    self.debugger.vm.pc = new_pc
        else:
            self.debugger.vm.pc += len(self.debugger.get_real_ops())

        self.print_current_op()

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
                value = ltree.value.lower()
                if value in FLAG_LITERALS:
                    if rhs is not True and rhs is not False:
                        print(
                            "Eval error: cannot assign non-boolean value to flag "
                            + "(use #t and #f instead)."
                        )
                        return

                    if value == "f_cb":
                        vm.flag_carry_block = rhs
                    elif value == "f_c":
                        vm.flag_carry = rhs
                    elif value == "f_v":
                        vm.flag_overflow = rhs
                    elif value == "f_z":
                        vm.flag_zero = rhs
                    elif value == "f_s":
                        vm.flag_sign = rhs
                    else:
                        raise RuntimeError("this should never happen!")
                else:
                    print("Eval error: cannot assign to symbol.")
            else:
                raise RuntimeError(
                    "unknown node type {}".format(ltree.__class__.__name__)
                )
        except HERAError as e:
            print("Eval error: " + str(e) + ".")

    def evaluate_node(self, node):
        vm = self.debugger.vm
        if isinstance(node, (IntNode, BoolNode)):
            return node.value
        elif isinstance(node, RegisterNode):
            if node.value == "pc":
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
                raise HERAError("undefined symbol `{}`".format(node.value))
        else:
            raise RuntimeError("unknown node type {}".format(node.__class__.__name__))

    def print_current_op(self):
        """Print the next operation to be executed. If the program has finished
        executed, nothing is printed.
        """
        if not self.debugger.is_finished():
            loc = self.debugger.program[self.debugger.vm.pc].loc
            print(str(loc.line) + "  " + loc.file_lines[loc.line - 1])
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

        print("[{}]\n".format(normalize_path(loc.path)))
        for i in range(lo, hi):
            prefix = "->  " if i == lineno else "    "
            print(prefix, end="")
            print(pad(str(i + 1), max_lineno_width), end="")

            line = lines[i].rstrip()
            if line:
                print("  " + line)
            else:
                print()

    def print_symbol(self, k, v):
        if isinstance(v, Label):
            suffix = " (label)"
        elif isinstance(v, DataLabel):
            suffix = " (data label)"
        elif isinstance(v, Constant):
            suffix = " (constant)"
        else:
            suffix = ""
        print("{} = {}".format(k, v) + suffix)

    def print_op(self, index):
        op = self.debugger.program[index].original
        prefix = "-> " if index == self.debugger.vm.pc else "   "
        print(prefix + "{:0>4x}  {}".format(index, op_to_string(op)), end="")

        # Print all labels pointing to the line.
        labels = self.debugger.get_labels(index)
        if labels:
            print(" [{}]".format(", ".join(labels)))
        else:
            print()


def normalize_path(path):
    # TODO: Should this just be done in the parser?
    return "<stdin>" if path == "-" else path


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

    list <n>        Print the current lines of source code and the n previous
                    and next lines. If not provided, n defaults to 3.

    ll              Print the entire program.

    next            Execute the current line.

    print <x>       Print the value of x.

    restart         Restart the execution of the program from the beginning.

    skip <loc>      Skip ahead to the given location.

    step            Step over the execution of a function.

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
    R1 = 42
    M[R7] = R4
    M[0xabc] = 0o123
    R7 = some_label""",
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
  function call, use `step` instead.""",
    # print
    "print": """\
print <x>:
  Print the value of x, which may be a register, a memory location, the
  program counter, or a symbol.

  Examples:
    print R7
    print M[0xc]
    print some_label
    print M[M[M[R1]]]""",
    # restart
    "restart": """\
restart:
  Restart execution of the program from the beginning. All registers and
  memory cells are reset.""",
    # skip
    "skip": """\
skip:
  Skip the current instruction.

skip <loc>:
  Skip to the given location (either a line number or a label) without
  executing any of the intermediate instructions.

skip +<n>:
  Skip the next `n` instructions without executing them.""",
    # step
    "step": """\
step:
  Step over the execution of a function. The step command is only valid when
  the current instruction is CALL.""",
    # quit
    "quit": """\
quit:
  Exit the debugger.""",
}
