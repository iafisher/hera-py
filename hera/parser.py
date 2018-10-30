"""Parse HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: October 2018
"""
from collections import namedtuple

from lark import Lark, Transformer, Tree


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
        elif matches[0].type == 'REGISTER':
            return int(matches[0][1:])
        else:
            return matches[0]


_parser = Lark(r'''
    ?start: op*

    op: SYMBOL "(" _arglist? ")"

    _arglist: ( value "," )* value

    value: DECIMAL | HEX | REGISTER

    SYMBOL: /[A-Za-z_][A-Za-z0-9_]*/
    DECIMAL: /-?[0-9]+/
    HEX: /-?0x[0-9a-fA-F]+/
    REGISTER: /[rR][0-9]+/

    // TODO: Support multi-line comments
    COMMENT: ( "//" /[^\n]*/ | "/*" /([^*]|\*[^\/])*/ "*/" )

    %import common.WS
    %ignore WS
    %ignore COMMENT
''', parser='lalr', transformer=TreeToOplist())


def parse(text):
    """Parse a HERA program into a list of Op objects."""
    tree = _parser.parse(text)
    if isinstance(tree, Tree):
        return tree.children
    else:
        return [tree]
