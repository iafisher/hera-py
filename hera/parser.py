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
from typing import List, Tuple

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
    parser = Parser(settings)
    program = parser.parse(Lexer(text, path=path))
    return (program, parser.messages)


class Parser:
    def __init__(self, settings: Settings) -> None:
        self.visited = set()
        self.settings = settings
        self.messages = Messages()

    def parse(self, lexer: Lexer) -> List[AbstractOperation]:
        if lexer.path:
            self.visited.add(get_canonical_path(lexer.path))

        try:
            ops = self.match_program(lexer)
        except HERAError as e:
            self.messages.err(*e.args)
            return []

        # Make sure to capture any warnings from the lexer.
        self.messages.extend(lexer.messages)
        return ops

    def match_program(self, lexer):
        expecting_brace = False
        ops = []
        while lexer.tkn.type != Token.EOF:
            msg = "expected HERA operation or #include"
            if not self.expect(lexer, (Token.INCLUDE, Token.SYMBOL, Token.RBRACE), msg):
                self.skip_until(lexer, {Token.INCLUDE, Token.SYMBOL})
                continue

            if lexer.tkn.type == Token.INCLUDE:
                ops.extend(self.match_include(lexer))
            elif lexer.tkn.type == Token.SYMBOL:
                name_tkn = lexer.tkn
                lexer.next_token()
                # Many legacy HERA program are enclosed with void HERA_main() { ... },
                # which is handled here.
                if lexer.tkn.type == Token.SYMBOL and name_tkn.value == "void":
                    expecting_brace = True
                    self.handle_cpp_boilerplate(lexer)
                elif lexer.tkn.type == Token.LPAREN:
                    op = self.match_op(lexer, name_tkn)
                    if op:
                        ops.append(op)
                    # Operations may optionally be separated by semicolons.
                    if lexer.tkn.type == Token.SEMICOLON:
                        lexer.next_token()
                else:
                    self.err("expected left parenthesis", lexer.tkn)
            else:
                if expecting_brace:
                    expecting_brace = False
                else:
                    self.err("unexpected right brace", lexer.tkn)
                lexer.next_token()

        return ops

    def match_op(self, lexer, name_tkn):
        """Match an operation, assuming that lexer.tkn is on the left parenthesis."""
        lexer.next_token()
        args = self.match_optional_arglist(lexer)
        lexer.next_token()
        try:
            cls = name_to_class[name_tkn.value]
        except KeyError:
            self.err("unknown instruction `{}`".format(name_tkn.value), name_tkn)
            return None
        else:
            return cls(*args, loc=name_tkn)

    VALUE_TOKENS = (Token.INT, Token.REGISTER, Token.SYMBOL, Token.STRING, Token.CHAR)

    def match_optional_arglist(self, lexer):
        if lexer.tkn.type == Token.RPAREN:
            return []

        args = []
        while True:
            if not self.expect(lexer, self.VALUE_TOKENS, "expected value"):
                self.skip_until(lexer, (Token.COMMA, Token.RPAREN))
                if lexer.tkn.type == Token.COMMA:
                    lexer.next_token()
                    continue
                else:
                    break

            if lexer.tkn.type == Token.INT:
                # Detect zero-prefixed octal numbers.
                prefix = lexer.tkn.value[:2]
                if len(prefix) == 2 and prefix[0] == "0" and prefix[1].isdigit():
                    base = 8
                    if self.settings.warn_octal_on:
                        self.warn(
                            'consider using "0o" prefix for octal numbers', lexer.tkn
                        )
                else:
                    base = 0

                try:
                    arg_as_int = int(lexer.tkn.value, base=base)
                except ValueError:
                    self.err("invalid integer literal", lexer.tkn)
                else:
                    lexer.tkn.value = arg_as_int
                    args.append(lexer.tkn)
                lexer.next_token()
            elif lexer.tkn.type == Token.CHAR:
                args.append(
                    Token(Token.INT, ord(lexer.tkn.value), location=lexer.tkn.location)
                )
                lexer.next_token()
            elif lexer.tkn.type == Token.REGISTER:
                try:
                    i = register_to_index(lexer.tkn.value)
                except HERAError:
                    self.err(
                        "{} is not a valid register".format(lexer.tkn.value), lexer.tkn
                    )
                else:
                    lexer.tkn.value = i
                    args.append(lexer.tkn)
                lexer.next_token()
            else:
                args.append(lexer.tkn)
                lexer.next_token()

            if lexer.tkn.type == Token.RPAREN:
                break
            elif lexer.tkn.type != Token.COMMA:
                self.err("expected comma or right parenthesis", lexer.tkn)
                self.skip_until(lexer, (Token.COMMA, Token.RPAREN))
                if lexer.tkn.type == Token.EOF or lexer.tkn.type == Token.RPAREN:
                    break
            else:
                lexer.next_token()
        return args

    def match_include(self, lexer):
        root_path = lexer.path
        tkn = lexer.next_token()
        msg = "expected quote or angle-bracket delimited string"
        if not self.expect(lexer, (Token.STRING, Token.BRACKETED), msg):
            lexer.next_token()
            return []

        lexer.next_token()
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
                sublexer = Lexer(included_text, path=include_path)
                return self.parse(sublexer)
        else:
            return self.expand_angle_include(lexer, tkn)

    def handle_cpp_boilerplate(self, lexer):
        lexer.next_token()
        if self.expect(lexer, Token.LPAREN, "expected left parenthesis"):
            lexer.next_token()

        if self.expect(lexer, Token.RPAREN, "expected right parenthesis"):
            lexer.next_token()

        self.expect(lexer, Token.LBRACE, "expected left curly brace")
        lexer.next_token()

    def expand_angle_include(self, lexer, include_path):
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

        sublexer = Lexer(included_text, path=include_path.value)
        return self.parse(sublexer)

    def expect(self, lexer, types, msg="unexpected token"):
        if isinstance(types, str):
            types = {types}

        if lexer.tkn.type not in types:
            if lexer.tkn.type == Token.EOF:
                self.err("premature end of input", lexer.tkn)
            else:
                self.err(msg, lexer.tkn)

            return False
        else:
            return True

    def skip_until(self, lexer, types):
        types = set(types)
        types.add(Token.EOF)
        while lexer.tkn.type not in types:
            lexer.next_token()

    def err(self, msg, tkn):
        self.messages.err(msg, tkn.location)

    def warn(self, msg, tkn):
        self.messages.warn(msg, tkn.location)


def get_canonical_path(fpath):
    if fpath == "-" or fpath == "<string>":
        return fpath
    else:
        return os.path.realpath(fpath)
