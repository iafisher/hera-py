from hera.checker import check
from hera.data import State
from hera.parser import parse


def helper(vm, opstr):
    # A little abstraction for the test suite, in case the virtual machine's API
    # changes.
    oplist, messages = parse(opstr)
    assert not messages.errors
    program, messages = check(oplist, State())
    assert not messages.errors

    # Take first op, or first data statement if there are no ops.
    op = (program.code + program.data)[0]
    vm.exec_one(op)
