# hera-py

[![Build Status](https://travis-ci.com/iafisher/hera-py.png)](https://travis-ci.com/iafisher/hera-py)
[![Coverage Status](https://coveralls.io/repos/github/iafisher/hera-py/badge.svg?branch=master)](https://coveralls.io/github/iafisher/hera-py?branch=master)

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
