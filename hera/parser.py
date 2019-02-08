"""The parser for the HERA language.

Abstract grammar:
  start := (op | include)*

  op      := SYMBOL LPAREN arglist? RPAREN
  include := INCLUDE (STRING | BRACKETED)

  arglist := (value COMMA)* value


Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import os.path
from typing import List, Optional, Set, Tuple, Union  # noqa: F401

from .data import HERAError, Messages, Settings, Token
from .lexer import Lexer
from .op import AbstractOperation, name_to_class
from .stdlib import TIGER_STDLIB_STACK, TIGER_STDLIB_STACK_DATA
from .utils import read_file, register_to_index


def parse(
    text: str, *, path=None, settings=Settings()
) -> Tuple[List[AbstractOperation], Messages]:
    """Parse a HERA program.

    `path` is the path of the file being parsed, as it will appear in error and
    warning messages. It defaults to "<string>".
    """
    lexer = Lexer(text, path=path)
    parser = Parser(lexer, settings)
    program = parser.parse()
    return (program, parser.messages)


class Parser:
    def __init__(self, lexer: Lexer, settings: Settings) -> None:
        self.lexer = lexer
        self.visited = set()  # type: Set[str]
        self.settings = settings
        self.messages = Messages()

    def parse(self) -> List[AbstractOperation]:
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

    def match_program(self) -> List[AbstractOperation]:
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
                # Many legacy HERA program are enclosed with void HERA_main() { ... },
                # which is handled here.
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

    def match_op(self, name_tkn: Token) -> Optional[AbstractOperation]:
        """Match an operation, assuming that self.lexer.tkn is on the left parenthesis.
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

    VALUE_TOKENS = {Token.INT, Token.REGISTER, Token.SYMBOL, Token.STRING, Token.CHAR}

    def match_optional_arglist(self) -> Optional[List[Token]]:
        """Match zero or more comma-separated values. Exits with the right parenthesis
        as the current token. Make sure to distinguish between a None return value (the
        arglist could not be parsed) and a [] return value (an empty arglist was parsed
        successfully).
        """
        if self.lexer.tkn.type == Token.RPAREN:
            return []

        args = []
        hit_error = False
        while True:
            if not self.expect(self.VALUE_TOKENS, "expected value"):
                hit_error = True
                self.skip_until({Token.COMMA, Token.RPAREN})
                if self.lexer.tkn.type == Token.COMMA:
                    self.lexer.next_token()
                    continue
                else:
                    break

            val = self.match_value()
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

    def match_value(self) -> Token:
        if self.lexer.tkn.type == Token.INT:
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
        else:
            return self.lexer.tkn

    def match_include(self) -> List[AbstractOperation]:
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

    def expand_angle_include(self, include_path: Token) -> List[AbstractOperation]:
        # There is no check for recursive includes in this function, under the
        # assumption that system libraries do not have recursive includes.
        if include_path.value == "HERA.h":
            self.warn("#include <HERA.h> is not necessary for hera-py", include_path)
            return []
        elif include_path.value == "Tiger-stdlib-stack-data.hera":
            included_text = TIGER_STDLIB_STACK_DATA
        elif include_path.value == "Tiger-stdlib-stack.hera":
            included_text = TIGER_STDLIB_STACK
        else:
            root_path = os.environ.get("HERA_C_DIR", "/home/courses/lib/HERA-lib")
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

    def expect(self, types: Union[str, Set[str]], msg="unexpected token") -> bool:
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

    def skip_until(self, types: Set[str]) -> None:
        types.add(Token.EOF)
        while self.lexer.tkn.type not in types:
            self.lexer.next_token()

    def err(self, msg: str, tkn: Optional[Token] = None) -> None:
        if tkn is None:
            tkn = self.lexer.tkn
        self.messages.err(msg, tkn.location)

    def warn(self, msg: str, tkn: Optional[Token] = None) -> None:
        if tkn is None:
            tkn = self.lexer.tkn
        self.messages.warn(msg, tkn.location)


def get_canonical_path(fpath: str) -> str:
    if fpath == "-" or fpath == "<string>":
        return fpath
    else:
        return os.path.realpath(fpath)
