"""
start := (op | include)*

op      := SYMBOL LPAREN arglist? RPAREN
include := INCLUDE (STRING | BRACKETED)

arglist := (value COMMA)* value
"""
import os.path
from typing import List, Tuple

from hera.data import HERAError, IntToken, Messages, Op
from hera.lexer import Lexer, TOKEN
from .stdlib import TIGER_STDLIB_STACK, TIGER_STDLIB_STACK_DATA
from hera.utils import read_file


def parse(text: str, *, path=None) -> Tuple[List[Op], Messages]:
    """Parse a HERA program.

    `path` is the path of the file being parsed, as it will appear in error and
    warning messages. It defaults to "<string>".
    """
    parser = Parser()
    program = parser.parse(Lexer(text, path=path))
    return (program, parser.messages)


class Parser:
    def __init__(self):
        self.visited = set()
        self.messages = Messages()

    def parse(self, lexer):
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
        while lexer.tkn.type != TOKEN.EOF:
            if lexer.tkn.type == TOKEN.INCLUDE:
                ops.extend(self.match_include(lexer))
            elif lexer.tkn.type == TOKEN.SYMBOL:
                name = lexer.tkn
                lexer.next_token()
                # Many legacy HERA program are enclosed with void HERA_main() { ... },
                # which is handled here.
                if lexer.tkn.type == TOKEN.SYMBOL and name == "void":
                    if lexer.next_token().type == TOKEN.LPAREN:
                        lexer.next_token()
                    else:
                        self.err("expected left parenthesis", lexer.tkn)

                    if lexer.tkn.type == TOKEN.RPAREN:
                        lexer.next_token()
                    else:
                        self.err("expected right parenthesis", lexer.tkn)

                    if lexer.tkn.type != TOKEN.LBRACE:
                        self.err("expected left curly brace", lexer.tkn)

                    lexer.next_token()
                    expecting_brace = True
                    continue
                elif lexer.tkn.type == TOKEN.LPAREN:
                    ops.append(self.match_op(lexer, name))
                    # Operations may optionally be separated by semicolons.
                    if lexer.tkn.type == TOKEN.SEMICOLON:
                        lexer.next_token()
                else:
                    self.err("expected left parenthesis", lexer.tkn)
            elif expecting_brace and lexer.tkn.type == TOKEN.RBRACE:
                lexer.next_token()
                expecting_brace = False
            else:
                self.err("expected HERA operation or #include", lexer.tkn)
                break

        return ops

    def match_op(self, lexer, name):
        """Match an operation, assuming that lexer.tkn is on the left parenthesis."""
        lexer.next_token()
        args = self.match_optional_arglist(lexer)
        lexer.next_token()
        return Op(name, args)

    VALUE_TOKENS = (TOKEN.INT, TOKEN.REGISTER, TOKEN.SYMBOL, TOKEN.STRING, TOKEN.CHAR)

    def match_optional_arglist(self, lexer):
        if lexer.tkn.type == TOKEN.RPAREN:
            return []

        args = []
        while True:
            if lexer.tkn.type == TOKEN.INT:
                # Detect zero-prefixed octal numbers.
                prefix = lexer.tkn[:2]
                if len(prefix) == 2 and prefix[0] == "0" and prefix[1].isdigit():
                    base = 8
                    self.warn('consider using "0o" prefix for octal numbers', lexer.tkn)
                else:
                    base = 0

                try:
                    args.append(IntToken(lexer.tkn, loc=lexer.tkn.location, base=base))
                except ValueError:
                    self.err("invalid integer literal", lexer.tkn)
                lexer.next_token()
            elif lexer.tkn.type == TOKEN.CHAR:
                args.append(ord(lexer.tkn))
                lexer.next_token()
            elif lexer.tkn.type in self.VALUE_TOKENS:
                args.append(lexer.tkn)
                lexer.next_token()
            else:
                self.err("expected value", lexer.tkn)
                self.skip_until(lexer, (TOKEN.COMMA, TOKEN.RPAREN))
                if lexer.tkn.type == TOKEN.EOF:
                    break

            if lexer.tkn.type == TOKEN.RPAREN:
                break
            elif lexer.tkn.type != TOKEN.COMMA:
                self.err("expected comma or right parenthesis", lexer.tkn)
                self.skip_until(lexer, (TOKEN.COMMA, TOKEN.RPAREN))
                if lexer.tkn.type == TOKEN.EOF or lexer.tkn.type == TOKEN.RPAREN:
                    break
            else:
                lexer.next_token()
        return args

    def match_include(self, lexer):
        root_path = lexer.path
        tkn = lexer.next_token()
        lexer.next_token()
        if tkn.type == TOKEN.STRING:
            include_path = os.path.join(os.path.dirname(root_path), tkn)

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
        elif tkn.type == TOKEN.BRACKETED:
            return self.expand_angle_include(lexer, tkn)
        else:
            self.err("expected quote or angle-bracket delimited string", tkn)
            return []

    def expand_angle_include(self, lexer, include_path):
        # There is no check for recursive includes in this function, under the
        # assumption that system libraries do not have recursive includes.
        if include_path == "HERA.h":
            self.warn("#include <HERA.h> is not necessary for hera-py", include_path)
            return []
        elif include_path == "Tiger-stdlib-stack-data.hera":
            included_text = TIGER_STDLIB_STACK_DATA
        elif include_path == "Tiger-stdlib-stack.hera":
            included_text = TIGER_STDLIB_STACK
        else:
            root_path = os.environ.get("HERA_C_DIR", "/home/courses/lib/HERA-lib")
            try:
                included_text = read_file(os.path.join(root_path, include_path))
            except HERAError as e:
                self.err(str(e), include_path)
                return []

        sublexer = Lexer(included_text, path=include_path)
        return self.parse(sublexer)

    def skip_until(self, lexer, tkns):
        tkns = set(tkns)
        tkns.add(TOKEN.EOF)
        while lexer.tkn.type not in tkns:
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
