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
    debugging messages. It defaults to "<string>".

    `includes` determines what happens when an #include statement is encountered. If
    `includes` is True, then the #include statement is interpreted as it is by the C
    preprocessor, i.e. the file identified by #include's argument is read, parsed, and
    pasted in with the rest of the operations. If it is False, then the #include
    statement is retained as an Op object.
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

        ops = []
        while lexer.tkn.type != TOKEN.EOF:
            if lexer.tkn.type == TOKEN.INCLUDE:
                ops.extend(self.match_include(lexer))
            elif lexer.tkn.type == TOKEN.SYMBOL:
                ops.append(self.match_op(lexer))
            else:
                self.err(lexer.tkn, "expected HERA operation or #include")
                break
        return ops

    def match_op(self, lexer):
        name = lexer.tkn
        lexer.next_token()

        if lexer.tkn.type != TOKEN.LPAREN:
            self.err(lexer.tkn, "expected left parenthesis")
            return Op(name, [])
        else:
            lexer.next_token()

        args = self.match_optional_arglist(lexer)

        if lexer.tkn.type != TOKEN.RPAREN:
            self.err(lexer.tkn, "expected left parenthesis")
            return Op(name, args)
        else:
            lexer.next_token()

        return Op(name, args)

    VALUE_TOKENS = (TOKEN.INT, TOKEN.REGISTER, TOKEN.SYMBOL, TOKEN.STRING, TOKEN.CHAR)

    def match_optional_arglist(self, lexer):
        args = []
        while lexer.tkn.type != TOKEN.RPAREN:
            if lexer.tkn.type == TOKEN.INT:
                try:
                    args.append(IntToken(lexer.tkn, loc=lexer.tkn.location, base=0))
                except ValueError:
                    self.err(lexer.tkn, "invalid integer literal")
                    break
            elif lexer.tkn.type == TOKEN.CHAR:
                args.append(ord(lexer.tkn))
            elif lexer.tkn.type in self.VALUE_TOKENS:
                args.append(lexer.tkn)
            else:
                self.err(lexer.tkn, "expected value")
                break

            lexer.next_token()
            if lexer.tkn.type == TOKEN.RPAREN:
                break
            elif lexer.tkn.type != TOKEN.COMMA:
                self.err(lexer.tkn, "expected comma or right-parenthesis")
                lexer.next_token()
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
                self.err(tkn, "recursive include")
                return []

            try:
                included_text = read_file(include_path)
            except HERAError as e:
                self.err(tkn, str(e))
                return []
            else:
                sublexer = Lexer(included_text, path=include_path)
                return self.parse(sublexer)
        elif tkn.type == TOKEN.BRACKETED:
            return self.expand_angle_include(lexer, tkn)
        else:
            self.err(tkn, "expected quote or angle-bracket delimited string")
            return []

    def expand_angle_include(self, lexer, include_path):
        # There is no check for recursive includes in this function, under the
        # assumption that system libraries do not have recursive includes.
        if include_path == "HERA.h":
            self.warn(include_path, "#include <HERA.h> is not necessary for hera-py")
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
                self.err(include_path, str(e))
                return []

        sublexer = Lexer(included_text, path=include_path)
        return self.parse(sublexer)

    def err(self, tkn, msg):
        self.messages.err(msg, tkn.location)

    def warn(self, tkn, msg):
        self.messages.warn(msg, tkn.location)


def get_canonical_path(fpath):
    if fpath == "-" or fpath == "<string>":
        return fpath
    else:
        return os.path.realpath(fpath)
