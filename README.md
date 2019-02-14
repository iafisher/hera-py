# hera-py

[![Build Status](https://travis-ci.com/iafisher/hera-py.png)](https://travis-ci.com/iafisher/hera-py)
[![Coverage Status](https://coveralls.io/repos/github/iafisher/hera-py/badge.svg?branch=master)](https://coveralls.io/github/iafisher/hera-py?branch=master)
[![PyPI](https://img.shields.io/pypi/v/hera-py.svg?label=version)](https://pypi.org/project/hera-py/)

An interpreter for the [Haverford Educational RISC Architecture](http://cs.haverford.edu/resources/hera) (HERA) assembly language.

## Installation
You can install hera-py with pip:

```
$ pip3 install hera-py
```

## Usage
After installation, use the `hera` command to run a HERA program:

```
$ hera main.hera
```

Enter the interactive debugger with the `debug` subcommand:

```
$ hera debug main.hera
```

Assemble a HERA program into machine code:

```
$ hera assemble main.hera
```

You can also preprocess a HERA program without running it, to see how pseudo-instructions and labels are resolved to HERA code:

```
$ hera preprocess main.hera
```

## Comparison with HERA-C and Hassem
HERA-C is the current HERA interpreter used at Haverford. It is implemented as a shell-script wrapper around a set of C++ macros that expand HERA instructions into C++ code, which is then compiled by g++.

hera-py improves on HERA-C in the following areas:

  - Includes a purpose-built HERA debugger
  - Concise and accurate error messages
  - Ease of use
    - Cross-platform and easy to install
    - Configurable with command-line options
    - Does not create temporary files
    - Command name has six fewer letters than `HERA-C-Run`

hera-py also supports several features that HERA-C does not:
  - Setting registers to the value of a label
  - Detecting stack overflow
  - Multi-precision multiplication
  - Relative branching by a fixed integer value (e.g., `BRR(10)`)
  - Branching by the value of a register (e.g., `SET(R1, 20); BR(R1)`)
  - Detecting invalid relative branches

HERA-C has a few features that hera-py does not:
  - C-style #define macros (and more generally the ability to embed arbitrary C++ code in HERA programs)

hera-py generally runs faster than HERA-C on small and medium-sized programs, while HERA-C is faster for very large programs.

Hassem is the current HERA assembler used at Haverford. hera-py has better error messages than Hassem, allows the user greater control of output (e.g., with the `--stdout` flag), and fixes some Hassem bugs.

## Acknowledgements
Thank you to [Christopher Villalta](https://github.com/csvillalta) for valuable feedback on early iterations of this project.
