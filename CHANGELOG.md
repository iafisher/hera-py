# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**NOTE**: As permitted by semantic versioning, backward compatibility is NOT maintained for initial development, i.e. releases before 1.0.0.

## [Unreleased]
### Added
- Support for `PC_ret` and `FP_alt` named registers.
- Support for `#include` directive.

### Fixed
- DSKIP with a named constant argument works correctly.

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
