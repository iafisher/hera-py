"""
The parser for the HERA language. As an assembly language, HERA has quite a simple
syntax.

Abstract grammar:

  start   := (op | include)*
  op      := SYMBOL LPAREN arglist? RPAREN
  include := INCLUDE (STRING | BRACKETED)
  arglist := (value COMMA)* value

The lexical structure of the language is defined in `hera/lexer.py`.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: July 2019
"""
import os.path
import re

from .data import HERAError, Messages, Settings, Token
from .lexer import Lexer
from .op import AbstractOperation, name_to_class
from .stdlib import (
    TIGER_STDLIB_REG,
    TIGER_STDLIB_REG_DATA,
    TIGER_STDLIB_STACK,
    TIGER_STDLIB_STACK_DATA,
)
from .utils import Path, PATH_STRING, read_file, register_to_index


def parse(
    text: str, *, path=PATH_STRING, settings=Settings()
) -> "Tuple[List[AbstractOperation], Messages]":
    """
    Parse a HERA program.

    `path` is the path of the file being parsed, as it will appear in error and
    warning messages. It defaults to "<string>".
    """
    text = evaluate_ifdefs(text)
    lexer = Lexer(text, path=path)
    parser = Parser(lexer, settings)
    program = parser.parse()
    return (program, parser.messages)


class Parser:
    def __init__(self, lexer: Lexer, settings: Settings) -> None:
        self.lexer = lexer
        # Keep track of the set of files that have already been parsed, to avoid
        # infinite recursion through #include statements.
        self.visited = set()  # type: Set[str]
        self.settings = settings
        self.messages = Messages()

    def parse(self) -> "List[AbstractOperation]":
        if self.lexer.path:
            self.visited.add(get_canonical_path(self.lexer.path))

        try:
            ops = self.match_program()
        except HERAError as e:
            self.messages.err(*e.args)
            return []

        # Make sure to capture any warnings from the lexer.
        self.messages.extend(self.lexer.messages)
        return ops

    def match_program(self) -> "List[AbstractOperation]":
        """Match an entire program."""
        expecting_brace = False
        ops = []
        while self.lexer.tkn.type != Token.EOF:
            msg = "expected HERA operation or #include"
            if not self.expect({Token.INCLUDE, Token.SYMBOL, Token.RBRACE}, msg):
                self.skip_until({Token.INCLUDE, Token.SYMBOL})
                continue

            if self.lexer.tkn.type == Token.INCLUDE:
                ops.extend(self.match_include())
            elif self.lexer.tkn.type == Token.SYMBOL:
                name_tkn = self.lexer.tkn
                self.lexer.next_token()
                # Legacy HERA program are enclosed in void HERA_main() { ... }, which is
                # handled here.
                if self.lexer.tkn.type == Token.SYMBOL and name_tkn.value == "void":
                    expecting_brace = True
                    self.handle_cpp_boilerplate()
                elif self.lexer.tkn.type == Token.LPAREN:
                    op = self.match_op(name_tkn)
                    if op:
                        ops.append(op)
                    # Operations may optionally be separated by semicolons.
                    if self.lexer.tkn.type == Token.SEMICOLON:
                        self.lexer.next_token()
                else:
                    self.err("expected left parenthesis")
            else:
                if expecting_brace:
                    expecting_brace = False
                else:
                    self.err("unexpected right brace")
                self.lexer.next_token()

        return ops

    def match_op(self, name_tkn: Token) -> "Optional[AbstractOperation]":
        """
        Match an operation, assuming that self.lexer.tkn is on the left parenthesis.
        """
        self.lexer.next_token()
        args = self.match_optional_arglist()
        self.lexer.next_token()
        if args is None:
            return None

        try:
            cls = name_to_class[name_tkn.value]
        except KeyError:
            self.err("unknown instruction `{}`".format(name_tkn.value), name_tkn)
            return None
        else:
            return cls(*args, loc=name_tkn)

    VALUE_TOKENS = {
        Token.INT,
        Token.REGISTER,
        Token.SYMBOL,
        Token.STRING,
        Token.CHAR,
        Token.MINUS,
    }

    def match_optional_arglist(self) -> "Optional[List[Token]]":
        """
        Match zero or more comma-separated values. Exits with the right parenthesis as
        the current token. Make sure to distinguish between a None return value (the
        arglist could not be parsed) and a [] return value (an empty arglist was parsed
        successfully).
        """
        if self.lexer.tkn.type == Token.RPAREN:
            return []

        args = []
        hit_error = False
        while True:
            if self.expect(self.VALUE_TOKENS, "expected value"):
                val = self.match_value()
            else:
                val = None

            if val is None:
                hit_error = True
                self.skip_until({Token.COMMA, Token.RPAREN})
                if self.lexer.tkn.type == Token.COMMA:
                    self.lexer.next_token()
                    continue
                else:
                    break
            else:
                args.append(val)

            self.lexer.next_token()
            if self.lexer.tkn.type == Token.RPAREN:
                break
            elif self.lexer.tkn.type != Token.COMMA:
                hit_error = True
                self.err("expected comma or right parenthesis")
                self.skip_until({Token.COMMA, Token.RPAREN})
                if (
                    self.lexer.tkn.type == Token.EOF
                    or self.lexer.tkn.type == Token.RPAREN
                ):
                    break
            else:
                self.lexer.next_token()

        return args if not hit_error else None

    def match_value(self) -> "Optional[Token]":
        """Match a value (e.g., an integer, a register)."""
        if self.lexer.tkn.type == Token.INT:
            return self.match_int()
        elif self.lexer.tkn.type == Token.CHAR:
            return Token(
                Token.INT, ord(self.lexer.tkn.value), location=self.lexer.tkn.location
            )
        elif self.lexer.tkn.type == Token.REGISTER:
            try:
                i = register_to_index(self.lexer.tkn.value)
            except HERAError:
                self.err("{} is not a valid register".format(self.lexer.tkn.value))
                i = 0
            self.lexer.tkn.value = i
            return self.lexer.tkn
        elif self.lexer.tkn.type == Token.MINUS:
            self.lexer.next_token()
            if not self.expect(Token.INT, "expected integer"):
                return None
            else:
                ret = self.match_int()
                ret.value *= -1
                return ret
        else:
            return self.lexer.tkn

    def match_int(self) -> Token:
        """
        Match an integer literal. Binary, octal and hexadecimal literals are supported.
        """
        # Detect zero-prefixed octal numbers.
        prefix = self.lexer.tkn.value[:2]
        if len(prefix) == 2 and prefix[0] == "0" and prefix[1].isdigit():
            base = 8
            if self.settings.warn_octal_on:
                self.warn('consider using "0o" prefix for octal numbers')
        else:
            base = 0

        try:
            arg_as_int = int(self.lexer.tkn.value, base=base)
        except ValueError:
            self.err("invalid integer literal")
            # 1 is a neutral value that is valid anywhere an integer is.
            arg_as_int = 1
        self.lexer.tkn.value = arg_as_int
        return self.lexer.tkn

    def match_include(self) -> "List[AbstractOperation]":
        """Match an #include statement."""
        root_path = self.lexer.path
        tkn = self.lexer.next_token()
        msg = "expected quote or angle-bracket delimited string"
        if not self.expect({Token.STRING, Token.BRACKETED}, msg):
            self.lexer.next_token()
            return []

        self.lexer.next_token()
        if tkn.type == Token.STRING:
            include_path = os.path.join(os.path.dirname(root_path), tkn.value)

            if get_canonical_path(include_path) in self.visited:
                self.err("recursive include", tkn)
                return []

            try:
                included_text = read_file(include_path)
            except HERAError as e:
                self.err(str(e), tkn)
                return []
            else:
                old_lexer = self.lexer
                included_text = evaluate_ifdefs(included_text)
                self.lexer = Lexer(included_text, path=include_path)
                ops = self.parse()
                self.lexer = old_lexer
                return ops
        else:
            return self.expand_angle_include(tkn)

    def handle_cpp_boilerplate(self) -> None:
        self.lexer.next_token()
        if self.expect(Token.LPAREN, "expected left parenthesis"):
            self.lexer.next_token()

        if self.expect(Token.RPAREN, "expected right parenthesis"):
            self.lexer.next_token()

        self.expect(Token.LBRACE, "expected left curly brace")
        self.lexer.next_token()

    def expand_angle_include(self, include_path: Token) -> "List[AbstractOperation]":
        """
        Given a path to a system library from an #include <...> statement, retrieve
        the library, parse it, and return the HERA operations.
        """
        # There is no check for recursive includes in this function, under the
        # assumption that system libraries do not have recursive includes.
        if include_path.value == "HERA.h":
            self.warn("#include <HERA.h> is not necessary for hera-py", include_path)
            return []
        elif include_path.value == "Tiger-stdlib-stack-data.hera":
            included_text = TIGER_STDLIB_STACK_DATA
        elif include_path.value == "Tiger-stdlib-stack.hera":
            included_text = TIGER_STDLIB_STACK
        elif include_path.value == "Tiger-stdlib-reg-data.hera":
            included_text = TIGER_STDLIB_REG_DATA
        elif include_path.value == "Tiger-stdlib-reg.hera":
            included_text = TIGER_STDLIB_REG
        else:
            # If the library name is not a known library, look for it in a number of
            # defined places.
            root_path = os.environ.get(
                "HERA_PY_DIR",
                os.environ.get("HERA_C_DIR", "/home/courses/lib/HERA-lib"),
            )
            try:
                included_text = read_file(os.path.join(root_path, include_path.value))
            except HERAError as e:
                self.err(str(e), include_path)
                return []

        old_lexer = self.lexer
        self.lexer = Lexer(included_text, path=include_path.value)
        ops = self.parse()
        self.lexer = old_lexer
        return ops

    def expect(self, types: "Union[str, Set[str]]", msg="unexpected token") -> bool:
        """
        Expect the current token to be one of the types in `types`, and record an error
        and return False if it is not.
        """
        if isinstance(types, str):
            types = {types}

        if self.lexer.tkn.type not in types:
            if self.lexer.tkn.type == Token.EOF:
                self.err("premature end of input")
            elif self.lexer.tkn.type == Token.ERROR:
                self.err(self.lexer.tkn.value)
            else:
                self.err(msg)

            return False
        else:
            return True

    def skip_until(self, types: "Set[str]") -> None:
        """Keep consuming tokens until a token whose type is in `types` is reached."""
        types.add(Token.EOF)
        while self.lexer.tkn.type not in types:
            self.lexer.next_token()

    def err(self, msg: str, tkn: "Optional[Token]" = None) -> None:
        """Record an error. Note that this does not immediately print to the console."""
        if tkn is None:
            tkn = self.lexer.tkn
        self.messages.err(msg, tkn.location)

    def warn(self, msg: str, tkn: "Optional[Token]" = None) -> None:
        """
        Record a warning. Note that this does not immediately print to the console.
        """
        if tkn is None:
            tkn = self.lexer.tkn
        self.messages.warn(msg, tkn.location)


_ifdef_symbol = r"[A-Za-z_][A-Za-z0-9_]*"
_ifdef_tokens = (
    ("IFDEF", r"^\s*#ifdef\s+" + _ifdef_symbol + r"\s*$"),
    ("IFNDEF", r"^\s*#ifndef\s+" + _ifdef_symbol + r"\s*$"),
    ("ELSE", r"^\s*#else\s*$"),
    ("ENDIF", r"^\s*#endif\s*$"),
)
_ifdef_pattern = re.compile(
    "|".join("(?P<%s>%s)" % pair for pair in _ifdef_tokens), flags=re.MULTILINE
)


def evaluate_ifdefs(text):
    """
    For compatibility with the HERA-C interpreter written in C++, hera-py supports
    #ifdef <x> ... #else ... #endif and #ifndef statements. The only token defined by
    the hera-py interpreter is HERA_PY, so for instance in

      #ifdef HERA_PY
        ...
      #else
        ...
      #endif

    everything in the else clause will be stripped and may contain code that is not
    valid HERA, e.g. C++.
    """
    ret = []
    starting_at = 0
    # A stack of booleans indicating whether we should keep text in the current block.
    keeping = [True]
    for mo in _ifdef_pattern.finditer(text):
        if keeping[-1]:
            ret.append(text[starting_at : mo.start()])

        kind = mo.lastgroup
        value = mo.group()
        if kind == "IFDEF":
            word = value.split()[-1]
            if word == "HERA_PY":
                keeping.append(True)
            else:
                keeping.append(False)
        elif kind == "IFNDEF":
            word = value.split()[-1]
            if word != "HERA_PY":
                keeping.append(True)
            else:
                keeping.append(False)
        elif kind == "ELSE" and len(keeping) > 1:
            keeping[-1] = not keeping[-1]
        elif kind == "ENDIF" and len(keeping) > 1:
            keeping.pop()

        if keeping[-1]:
            starting_at = mo.end()

    ret.append(text[starting_at:])
    return "".join(ret)


def get_canonical_path(fpath: Path) -> str:
    if not isinstance(fpath, Path) or fpath.kind == Path.FILE:
        return Path(os.path.realpath(fpath))
    else:
        return fpath
