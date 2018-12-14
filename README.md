# hera-py

[![Build Status](https://travis-ci.com/iafisher/hera-py.png)](https://travis-ci.com/iafisher/hera-py)
[![Coverage Status](https://coveralls.io/repos/github/iafisher/hera-py/badge.svg?branch=master)](https://coveralls.io/github/iafisher/hera-py?branch=master)
[![PyPI](https://img.shields.io/pypi/v/hera-py.svg?label=version)](https://pypi.org/project/hera-py/)

An interpreter for the [Haverford Educational RISC Architecture](https://www.haverford.edu/computer-science/resources/hera) (HERA) assembly language.

## Installation
You can install hera-py with pip:

```
$ pip3 install hera-py
```

## Usage
After installation, hera-py can be invoked with the `hera` command to run a HERA program:

```
$ hera my-hera-file.hera
```

You can also preprocess a HERA program without running it, to see how pseudo-instructions and labels are resolved to HERA code:

```
$ hera preprocess my-hera-file.hera
```

### Comparison with HERA-C
HERA-C is the current HERA interpreter used as Haverford. It is implemented as a shell-script wrapper around a set of C++ macros that expand HERA instructions into C++ code. hera-py aims to improve on HERA-C in the following areas:
  - Ease of use
    - Cross-platform and easy to install
    - Configurable with command-line options
    - Does not create temporary files
    - Can read programs from stdin
    - Command name has six fewer letters than `HERA-C-Run`
  - Helpful error messages
  - Simple debugging

hera-py also supports several features that HERA-C does not:
  - Multi-precision multiplication
  - Relative branching by a fixed integer value (e.g., `BRR(10)`)
  - Branching by the value of a register (e.g., `SET(R1, 20); BR(R1)`)
  - Setting registers to the value of a label

HERA-C has a few features that hera-py does not:
  - C-style #define macros (and more generally the ability to embed arbitrary C++ code in HERA programs)
  - Relative branching to labels (though the same outcome can be achieved with register-mode branching)

## Design
Running a HERA program takes a few steps:

1. The text of the program is parsed into a list of instruction objects.  (`hera/parser.py`)
2. The symbol table for the program is generated.  (`hera/symtab.py`)
3. The program is type-checked to ensure that all operations take the proper number and type of operands.  (`hera/typechecker.py`)
4. Pseudo-instructions are converted into actual instructions, and labels and constants are substituted for their values.  (`hera/preprocessor.py`)
5. The instructions are executed on a virtual HERA machine.  (`hera/vm.py`)

For more details about the implementation, see the docstrings in each module.
