# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**NOTE**: As permitted by semantic versioning, backward compatibility is NOT maintained for initial development, i.e. releases before 1.0.0.

## [Unreleased]
Nothing yet.

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
