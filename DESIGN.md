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

Preprocessing is the step in which assembly-language features like labels and
named constants, and pseudo-operations like `SET` and `CMP`, are converted
into strict HERA code. The preprocessing step is part of the interpreter,
debugger, and assembler workflow.

## Organization of the Python package
The entry point into hera-py is defined in `hera/main.py`. The most important
module is `hera/op.py`, which defines every HERA operation, its encoding in
binary, its parameter types, and its semantics. The HERA virtual machine is
defined in `hera/vm.py`. Most of the other modules define the imperative
functions of hera-py, depending heavily on the declarations in `hera/op.py`.
For more details, read the docstrings of each module.

## Error handling
Functions in hera-py often need to return multiple errors, for which the
standard Python exception mechanism is not sufficient. Borrowing a technique
from Rust and Go, hera-py functions often return a tuple of (ret, errors),
where `ret` is the regular return value and `errors` is a `Messages` object
(defined in `hera/data.py`) that lists the warnings and errors that the
function generated.

## How to add a new operation
To add a new HERA operation:

1. Define a class in `hera/op.py` that inherits from `AbstractOperation`, and follow
   the instructions in the docstring of each method of that class as to whether your
   subclass should override it or not.
2. Add your class to the `name_to_class` dictionary in `hera/op.py`.

To add a new pseudo-operation:

1. Define a class in `hera/op.py` that inherits from `AbstractOperation`, and follow
   the instructions in the docstring of each method of that class as to whether your
   subclass should override it or not.
2. Add a case for it in the `operation_length` function in `hera/checker.py`.

## Code style
hera-py is formatted according to the default settings of
[Black](https://github.com/ambv/black). Note that by default Black requires
that lines do not exceed 88 characters, and that string literals are delimited
by double quotes.

Every module and non-trivial function should have a docstring. Docstrings
should always be delimited by three double quotes. Multi-line docstrings
should have the two delimiters on separate lines, e.g.

```
def add(x, y):
    """
    Add two numbers together and return their sum. The arguments may be either
    integers or floating-point numbers.
    """
    ...
```
