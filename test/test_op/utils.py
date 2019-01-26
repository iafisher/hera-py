from hera.op import resolve_ops
from hera.parser import parse
from hera.preprocessor import preprocess


def helper(vm, opstr):
    # A little abstraction for the test suite, in case the virtual machine's API
    # changes.
    ops = resolve_ops(parse(opstr))
    vm.exec_one(ops[0])
