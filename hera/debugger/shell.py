from typing import Dict, List

from . import minilanguage
from .debugger import Debugger
from .minilanguage import AssignNode, IntNode, MemoryNode, RegisterNode, SymbolNode
from hera.data import HERAError, Op
from hera.loader import load_program
from hera.typechecker import Constant, DataLabel, Label
from hera.utils import BRANCHES, DATA_STATEMENTS, op_to_string, print_register_debug


_HELP_MSG = """\
Available commands:
    break <n>     Set a breakpoint on the n'th line of the program. When no
                  arguments are given, all current breakpoints are printed.

    continue      Execute the program until a breakpoint is encountered or the
                  program terminates.

    execute <op>  Execute a HERA operation. Only non-branching operations may
                  be executed.

    help          Print this help message.

    list <n>      Print the current lines of source code and the n previous and
                  next lines. If not provided, n defaults to 3.

    longlist      Print the entire program.

    next          Execute the current line.

    restart       Restart the execution of the program from the beginning.

    skip <n>      Skip the next n instructions without executing them. If not
                  provided, n defaults to 1.

    symbols       Print all symbols the debugger is aware of.

    quit          Exit the debugger.

Command names can generally be abbreviated with a unique prefix, e.g. "n" for
"next".
"""


def debug(program: List[Op], symbol_table: Dict[str, int]) -> None:
    """Start the debug loop."""
    debugger = Debugger(program, symbol_table)
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
            cmd, line = response.split(maxsplit=1)
        except ValueError:
            cmd = response
            line = ""

        args = line.split()
        cmd = cmd.lower()
        if "break".startswith(cmd):
            self.handle_break(args)
        elif "continue".startswith(cmd):
            self.handle_continue(args)
        elif "execute".startswith(cmd):
            self.handle_execute(line)
        elif "list".startswith(cmd):
            self.handle_list(args)
        elif cmd == "longlist" or cmd == "ll":
            self.handle_long_list(args)
        elif "next".startswith(cmd):
            self.handle_next(args)
        elif "restart".startswith(cmd):
            self.handle_restart(args)
        elif cmd == "rr":
            self.handle_rr(args)
        elif "skip".startswith(cmd):
            self.handle_skip(args)
        elif cmd.startswith("sym") and "symbols".startswith(cmd):
            self.handle_symbols(args)
        elif "help".startswith(cmd):
            print(_HELP_MSG)
        else:
            self.handle_expression(response)

    def handle_break(self, args):
        if len(args) > 1:
            print("break takes zero or one arguments.")
            return

        # TODO: In pdb, break with no arguments set a breakpoint at the current
        # line. Should I do that too?
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

    def handle_next(self, args):
        if len(args) != 0:
            print("next takes no arguments.")
            return

        if self.debugger.is_finished():
            print("Program has finished executing. Enter 'r' to restart.")
            return

        self.debugger.exec_ops(1)
        self.print_current_op()

    def handle_symbols(self, args):
        if len(args) != 0:
            print("symbols takes no arguments.")
            return

        sorted_pairs = sorted(
            self.debugger.symbol_table.items(), key=lambda t: t[0].lower()
        )
        for k, v in sorted_pairs:
            self.print_symbol(k, v)

    def handle_skip(self, args):
        if len(args) > 1:
            print("skip takes zero or one arguments.")
            return

        if len(args) == 1:
            try:
                offset = int(args[0])
            except ValueError:
                print("skip takes an integer argument.")
        else:
            offset = 1

        # TODO: This behavior doesn't match the command's help description.
        self.debugger.exec_ops(offset)
        self.print_current_op()

    def handle_execute(self, line):
        try:
            ops, _ = load_program(line)
        except SystemExit:
            return

        for op in ops:
            if op.name in BRANCHES or op.name in ("CALL", "RETURN"):
                print("execute cannot take branching operations.")
                return
            elif op.name in DATA_STATEMENTS:
                print("execute cannot take data statements.")
                return

        vm = self.debugger.vm
        opc = vm.pc
        for op in ops:
            vm.exec_one(op)
        vm.pc = opc

    def handle_list(self, args):
        if len(args) > 1:
            print("list takes zero or one arguments.")
            return

        try:
            context = int(args[0], base=0) if args else 3
        except ValueError:
            print("Could not parse argument to list.")
            return

        previous_ops = self.debugger.get_previous_ops(context)
        next_ops = self.debugger.get_next_ops(context)

        program = self.debugger.program
        vm = self.debugger.vm

        first_op = previous_ops[0][1] if previous_ops else program[vm.pc]
        last_op = next_ops[-1][1] if next_ops else program[vm.pc]

        if first_op.name.location is not None:
            path = (
                "<stdin>"
                if first_op.name.location.path == "-"
                else first_op.name.location.path
            )
            first_line = first_op.name.location.line
            last_line = last_op.name.location.line
            print("[{}, lines {}-{}]\n".format(path, first_line, last_line))

        for pc, _ in previous_ops:
            self.print_op(pc)

        self.print_op(vm.pc)

        for pc, _ in next_ops:
            self.print_op(pc)

    def handle_long_list(self, args):
        if len(args) != 0:
            print("longlist takes no arguments.")
            return

        index = 0
        program = self.debugger.program
        while index < len(program):
            original = program[index].original
            self.print_op(index)
            while index < len(program) and program[index].original == original:
                index += 1

    def handle_continue(self, args):
        if len(args) != 0:
            print("continue takes no arguments.")
            return

        self.debugger.exec_ops(len(self.debugger.program))
        self.print_current_op()

    def handle_restart(self, args):
        if len(args) != 0:
            print("restart takes no arguments.")
            return

        self.debugger.reset()
        self.print_current_op()

    def handle_rr(self, args):
        if len(args) != 0:
            print("rr takes no arguments.")
            return

        vm = self.debugger.vm
        if all(r == 0 for r in vm.registers):
            print("All registers are set to zero.")
        else:
            last_non_zero = 15
            while vm.registers[last_non_zero] == 0:
                last_non_zero -= 1

            if last_non_zero < 13:
                for i in range(1, last_non_zero + 1):
                    print_register_debug("R" + str(i), vm.registers[i], to_stderr=False)
                print("\nAll higher registers are set to zero.")
            else:
                for i, v in enumerate(vm.registers[1:], start=1):
                    print_register_debug("R" + str(i), v, to_stderr=False)

    def handle_expression(self, line):
        try:
            tree = minilanguage.parse(line)
        except SyntaxError as e:
            msg = str(e)
            if msg:
                print("Parse error: " + msg + ".")
            else:
                print("Parse error.")
            return

        vm = self.debugger.vm
        try:
            if isinstance(tree, AssignNode):
                rhs = self.evaluate_node(tree.rhs)
                if isinstance(tree.lhs, RegisterNode):
                    if tree.lhs.value == "pc":
                        vm.pc = rhs
                    else:
                        vm.store_register(tree.lhs.value, rhs)
                else:
                    address = self.evaluate_node(tree.lhs.address)
                    vm.assign_memory(address, rhs)
            elif isinstance(tree, RegisterNode):
                if tree.value == "pc":
                    print("PC = {}".format(vm.pc))
                else:
                    value = vm.get_register(tree.value)
                    print_register_debug(tree.value, value, to_stderr=False)
            elif isinstance(tree, MemoryNode):
                address = self.evaluate_node(tree.address)
                print("M[{}] = {}".format(address, vm.access_memory(address)))
            elif isinstance(tree, SymbolNode):
                try:
                    v = self.debugger.symbol_table[tree.value]
                except KeyError:
                    print(
                        "{} is not a recognized command or symbol.".format(tree.value)
                    )
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

    def evaluate_node(self, node):
        vm = self.debugger.vm
        if isinstance(node, IntNode):
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
        program = self.debugger.program
        vm = self.debugger.vm
        if not self.debugger.is_finished():
            op = program[vm.pc].original or program[vm.pc]
            opstr = op_to_string(op)
            if op.name.location is not None:
                path = (
                    "<stdin>" if op.name.location.path == "-" else op.name.location.path
                )
                print("[{}, line {}]\n".format(path, op.name.location.line))
            print("{:0>4x}  {}".format(vm.pc, opstr))
        else:
            print("Program has finished executing.")

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
