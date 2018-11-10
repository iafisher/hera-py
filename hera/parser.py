"""Parse HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""
import re
from collections import namedtuple

from lark import Lark, Token, Transformer, Tree


Op = namedtuple('Op', ['name', 'args'])


class TreeToOplist(Transformer):
    """Transform Lark's parse tree into a list of HERA ops."""

    def op(self, matches):
        return Op(matches[0], matches[1:])

    def value(self, matches):
        if matches[0].type == 'DECIMAL':
            return int(matches[0])
        elif matches[0].type == 'HEX':
            return int(matches[0], base=16)
        elif matches[0].type == 'OCTAL':
            return int(matches[0], base=8)
        elif matches[0].type == 'BINARY':
            return int(matches[0], base=2)
        elif matches[0].type == 'STRING':
            otkn = matches[0]
            s = replace_escapes(otkn[1:-1])
            ntkn = Token('STRING', s)
            # Preserve data from the original token.
            ntkn.pos_in_stream = otkn.pos_in_stream
            ntkn.line = otkn.line
            ntkn.column = otkn.column
            ntkn.end_line = otkn.end_line
            ntkn.end_column = otkn.end_column
            return ntkn
        else:
            return matches[0]


_parser = Lark(
    r'''
    ?start: op*

    op: SYMBOL "(" _arglist? ")"

    _arglist: ( value "," )* value

    value: DECIMAL | HEX | OCTAL | BINARY | REGISTER | SYMBOL | STRING

    REGISTER.2: /[rR][0-9]+/
    SYMBOL: /[A-Za-z_][A-Za-z0-9_]*/
    DECIMAL: /-?[0-9]+/
    HEX: /-?0x[0-9a-fA-F]+/
    // TODO: How should I handle zero-prefixed numbers, which the HERA-C
    // simulator would treat as octal?
    OCTAL: /-?0o[0-7]+/
    BINARY: /-?0b[01]+/
    STRING: /"(\\.|[^"])*"/

    COMMENT: ( "//" /[^\n]*/ | "/*" /([^*]|\*[^\/])*/ "*/" )

    %import common.WS
    %ignore WS
    %ignore COMMENT
    ''',
    parser='lalr',
    transformer=TreeToOplist()
)


def parse(text):
    """Parse a HERA program into a list of Op objects."""
    tree = _parser.parse(text)
    if isinstance(tree, Tree):
        return tree.children
    else:
        return [tree]


def replace_escapes(s):
    return re.sub(r'\\.', repl, s)


def repl(matchobj):
    c = matchobj.group(0)[1]
    if c == 'n':
        return '\n'
    elif c == 't':
        return '\t'
    elif c == '\\':
        return '\\'
    elif c == '"':
        return '"'
    else:
        # TODO: Give a warning for this.
        return '\\' + c
