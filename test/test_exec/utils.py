from hera.checker import check
from hera.data import Settings
from hera.parser import parse


def helper(vm, opstr):
    # A little abstraction for the test suite, in case the virtual machine's API
    # changes.
    oplist, messages = parse(opstr)
    assert not messages.errors, messages.errors[0]
    program, messages = check(oplist, Settings())
    assert not messages.errors, messages.errors[0]

    # Take first op, or first data statement if there are no ops.
    op = (program.code + program.data)[0]
    op.execute(vm)
