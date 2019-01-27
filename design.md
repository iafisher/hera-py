Running a HERA program takes a few steps:

1. The text of the program is parsed into a list of instruction objects.  (`hera/parser.py`)
2. The program is type-checked to ensure that all operations take the proper number and type of operands, and the symbol table is generated.  (`hera/checker.py` and `hera/op.py`)
3. Pseudo-instructions are converted into actual instructions, and labels and constants are substituted for their values.  (`hera/checker.py` and `hera/op.py`)
4. The instructions are executed on a virtual HERA machine.  (`hera/vm.py` and `hera/op.py`)

The HERA language itself is mostly implemented in `hera/op.py`. Each kind of HERA instruction (`SETLO`, `INC`, etc.) has its own class, which implements a few crucial methods: `typecheck` to check that its arguments have the expected types, `convert` to convert pseudo-operations into real operations, and `execute` to execute the operation on a HERA virtual machine.

For more details about the implementation, see the docstrings in each module.
