This document describes the design of hera-py. It is intended for developers
who wish to read or modify the hera-py codebase. Users of hera-py should
consult the project's README, the `hera` executable's help message, or the
Haverford CS Department's documentation on HERA.

## Top-level design
[hera-py](https://pypi.org/project/hera-py/) is a Python software package for
working with the Haverford Educational RISC Architecture (HERA) assembly
language. hera-py's public interface is the `hera` command-line executable
program, which wraps the following tools:

- An interpreter
- A debugger
- An assembler
- A disassembler
- A preprocessor

## Organization of the Python package
The entry point into hera-py is defined in `hera/main.py`. The most important
module is `hera/op.py`, which defines every HERA operation, its encoding in
binary, its parameter types, and its semantics. The HERA virtual machine is
defined in `hera/vm.py`. Most of the other modules define the imperative
functions of hera-py, depending heavily on the declarations in `hera/op.py`.
For more details, read the docstrings of each module.
