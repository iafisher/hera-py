# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**NOTE**: As permitted by semantic versioning, backward compatibility is NOT maintained for initial development, i.e. releases before 1.0.0.

## [0.5.2] - 2019-02-02
### Added
- The `warn-octal-off` flag.
- The `info` command now accepts one or more argument for specific aspects of the program state.
- The `info` command can now print information about the program's call stack.
- The `help` command now accepts abbreviated command names.

### Changed
- The `--no-ret-warn` flag has been renamed to `--warn-return-off`.
- The `--big-stack` and `--warn-return-off` flags can no longer be used with the `preprocess` subcommand.

### Fixed
- `hera-py` now installs with Python 3.4 without errors. I believe this was broken in version 0.5.1.
- The debugger now executes data statements on start-up.
- The `execute` debugging command now prints an error message when invoked with no arguments.

## [0.5.1] - 2019-01-31
### Added
- Arithmetic operations are supported in printing and assigning values in the debugger.
- Much more informative messages for parse errors.
- Detection of invalid return addresses, and accompanying `--no-ret-warn` flag.
- The `undo` debugging command.
- The `on` and `off` debugging commands for flag manipulation.
- The `next` debugging command now takes an optional argument.
- The `print` debugging command now takes accepts an optional format specifier argument.
- The `print` debugging command now takes multiple comma-separated arguments.
- Printing the program counter or `PC_ret` (`R13`) in the debugger now indicates what line of code the registers correspond to.
- The `--no-debug` command-line flag.

### Changed
- The `restart` debugging command may no longer be abbreviated.
- The `skip` debugging command has been renamed to `jump`.
- Debugger now prints three lines of context instead of one after commands that affect the program counter.
- The syntax for memory locations in the debugger minilanguage is now `@<address>` instead of `M[address]`.

### Removed
- The `+n` argument to the `jump` debugging command.
- Flags can no longer be printed with the `print` debugging command. Use the `info` command instead.
- Flags can no longer be changed with the `assign` debugging command. Use the new `on` and `off` commands instead.

### Fixed
- A label may no longer be the second argument to `RETURN`.
- The `assign` debugging command no longer prints a spurious error message when invoked.
- Negative numbers are parsed correctly in the debugging minilanguage.
- The debugger now respects the `--no-color` command-line flag.
- The printed register values after program execution now correctly print negative numbers under the signed interpretation of 16 bits.
- The `step` command no longer stops prematurely when the number of instructions executed exceeds the length of the program.
- Printing invalid registers in the debugger no longer crashes it.

## [0.5.0] - 2019-01-27
### Added
- Error messages for `#include` with non-existent file now print the line number.
- The `list` and `ll` debugging commands.
- The `execute` debugging command.
- The `info` debugging command.
- The `assign` debugging command, and its alias `x = y`.
- The `step` debugging command.
- The debugging expresson mini-language.
- A warning is printed when `R11` is used as the second argument of `NOT`.
- A warning is printed when `CALL` and `RETURN` are used with atypical registers.
- `help` debugging command takes one or more arguments and prints more detailed help messages for specific commands.
- `TIGER_STRING` is accepted as an alias for `LP_STRING`.
- `--big-stack` command-line flag.

### Changed
- Relative branch instructions can now target labels.
- Warning for zero-prefixed octal literals will only be printed once per program, rather than for every occurrence.
- Data statements may never follow code, even when in different files.
- ANSI colors are not used when standard error is not a tty-like device.
- Invalid backslash escapes in string literals are now errors.
- Newlines in string literals are no longer allowed.

### Fixed
- Use of undefined labels gives proper error message instead of Python exception.
- `continue` in debugger doesn't get stuck on breakpoints.
- `break` debugging command now accepts labels as arguments.
- Constants and data labels cannot be used as branch targets.
- Re-defined constants prevent execution, instead of just printing an error message.
- Passing too few parameters to SET no longer crashes the program.
- Constants can no longer be used before they are declared.
- Invalid zero-prefixed octal literals no longer crash the interpreter.
- Labels are calculated correctly after branches on registers.
- `skip` debugging command no longer executes instructions, matching its help description.
- Symbols beginning with "m" can now be printed in the debugger.
- Too few arguments to `CALL` op now causes an error message to be printed, instead of crashing the interpreter.
- Invalid backslash escapes in character literals now cause an error instead of crashing the interpreter.

### Removed
- The `--lines` command-line argument.


## [0.4.0] - 2019-01-02
### Added
- Interactive debugging!
- Support for `PC_ret` and `FP_alt` named registers.
- Support for `#include` directive.
- Runtime errors for use of SWI and RTI instructions now show line of code, and are only emitted once per program run.

### Fixed
- DSKIP with a named constant argument works correctly.
- Symbols (labels, constants and data labels) cannot be redefined.


## [0.3.0] - 2018-12-14
### Added
- Static type-checking.
- `--verbose` and `--quiet` flags.
- Zero-prefixed octal numbers (with a warning), for backwards compatibility with HERA-C.
- Limited support for the `SWI` and `RTI` operations.
- Character literals can be used in HERA code.

### Changed
- Order of flags in debugging output, to match HERA-C.
- Static data begins at memory address `0xc000`, per the HERA manual.

### Fixed
- Label names can begin with a valid register (e.g., `R1_INIT`).
- Data statements no longer cause labels to resolve to the incorrect line number.

### Removed
- `--no-dump-state` flag (use `--quiet` instead).


## [0.2.0] - 2018-11-14
### Added
- Data statements: `CONSTANT`, `DLABEL`, `INTEGER`, `LP_STRING`, and `DSKIP`.
- `SP` as an alias for `R15`.

### Changed
- The `assembly` subcommand has been renamed to `preprocess`.


## [0.1.1] - 2018-11-09
### Added
- Support for Python 3.4 and 3.5.


## [0.1.0] - 2018-11-09
Initial release with support for all HERA instructions and pseudo-instructions, excluding data statements.
