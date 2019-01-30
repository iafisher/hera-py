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
        ops = []
        while lexer.tkn.type != TOKEN.EOF:
            if lexer.tkn.type == TOKEN.INCLUDE:
                ops.extend(self.match_include(lexer))
            elif lexer.tkn.type == TOKEN.SYMBOL:
                ops.append(self.match_op(lexer))
            else:
                self.err(lexer, "expected operation or include")
                break
        return ops

    def match_op(self, lexer):
        name = lexer.tkn
        lexer.next_token()

        if lexer.tkn.type != TOKEN.LPAREN:
            self.err(lexer, "expected left parenthesis")
            return Op(name, [])
        else:
            lexer.next_token()

        args = self.match_optional_arglist(lexer)

        if lexer.tkn.type != TOKEN.RPAREN:
            self.err(lexer, "expected left parenthesis")
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
                    self.err(lexer, "invalid integer literal")
                    break
            elif lexer.tkn.type in self.VALUE_TOKENS:
                args.append(lexer.tkn)
            else:
                self.err(lexer, "expected value")
                break

            lexer.next_token()
            if lexer.tkn.type == TOKEN.RPAREN:
                break
            elif lexer.tkn.type != TOKEN.COMMA:
                self.err(lexer, "expected comma or right-parenthesis")
                lexer.next_token()
                break
            else:
                lexer.next_token()
        return args

    def match_include(self, lexer):
        self.lexer.next_token()
        if lexer.tkn.type == TOKEN.STRING:
            include_path = lexer.tkn[1:-1]
            root_path = lexer.path
            include_path = os.path.join(os.path.dirname(root_path), include_path)

            if get_canonical_path(include_path) in self.visited:
                self.messages.err("recursive include")
                return []

            try:
                included_text = read_file(include_path)
            except HERAError as e:
                self.messages.err(str(e))
                return []
            else:
                sublexer = Lexer(included_text, path=include_path)
                return self.parse(sublexer)
        elif lexer.tkn.type == TOKEN.BRACKETED:
            raise NotImplementedError
        else:
            self.err(lexer, "expected quote or angle-bracket delimited string")
            return []

    def err(self, lexer, msg):
        self.messages.err(msg, lexer.get_location())


def get_canonical_path(fpath):
    if fpath == "-" or fpath == "<string>":
        return fpath
    else:
        return os.path.realpath(fpath)
