"""Parse HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
import re
from collections import namedtuple

from lark import Lark, Token, Transformer, Tree
from lark.exceptions import LarkError, UnexpectedCharacters, UnexpectedToken

from .utils import emit_warning, HERAError, IntToken


Op = namedtuple("Op", ["name", "args"])


class TreeToOplist(Transformer):
    """Transform Lark's parse tree into a list of HERA ops."""

    def cpp_program(self, matches):
        emit_warning("void HERA_main() { ... } is not necessary")
        return matches

    def op(self, matches):
        return Op(matches[0], matches[1:])

    def value(self, matches):
        line = matches[0].line
        column = matches[0].column

        if matches[0].type == "DECIMAL":
            return IntToken(matches[0], line=line, column=column)
        elif matches[0].type == "HEX":
            return IntToken(matches[0], base=16, line=line, column=column)
        elif matches[0].type == "OCTAL":
            if not matches[0].startswith("0o"):
                emit_warning(
                    "zero-prefixed numbers are interpreted as octal",
                    line=matches[0].line,
                    column=matches[0].column,
                )
            return IntToken(matches[0], base=8, line=line, column=column)
        elif matches[0].type == "BINARY":
            return IntToken(matches[0], base=2, line=line, column=column)
        elif matches[0].type == "STRING":
            otkn = matches[0]
            s = replace_escapes(otkn[1:-1])
            ntkn = Token("STRING", s)
            # Preserve data from the original token.
            ntkn.pos_in_stream = otkn.pos_in_stream
            ntkn.line = otkn.line
            ntkn.column = otkn.column
            ntkn.end_line = otkn.end_line
            ntkn.end_column = otkn.end_column
            return ntkn
        elif matches[0].type == "SYMBOL":
            if is_register(matches[0]):
                matches[0].type = "REGISTER"
            return matches[0]
        else:
            return matches[0]


def is_register(s):
    return (s[0] in "rR" and s[1:].isdigit()) or s in ("Rt", "FP", "SP")


_parser = Lark(
    r"""
    ?start: cpp_program | _hera_program

    cpp_program: _INCLUDE* _cpp_open op* _CPP_CLOSE
    _hera_program: op*

    // Underscores before everything so that no tokens end up in the tree.
    _INCLUDE: /#include.*/
    _cpp_open: "void" _SYMBOL "(" ")" "{"
    _CPP_CLOSE: "}"
    _SYMBOL: SYMBOL

    op: SYMBOL "(" _arglist? ")" ";"?

    _arglist: ( value "," )* value

    value: DECIMAL | HEX | OCTAL | BINARY | SYMBOL | STRING

    SYMBOL: /[A-Za-z_][A-Za-z0-9_]*/
    DECIMAL: /-?[1-9][0-9]*/ | "0"
    HEX.2: /-?0x[0-9a-fA-F]+/
    OCTAL.2: /-?0o[0-7]+/ | /-?0[1-9]+/
    BINARY.2: /-?0b[01]+/
    STRING: /"(\\.|[^"])*"/

    COMMENT: ( "//" /[^\n]*/ | "/*" /([^*]|\*[^\/])*/ "*/" )

    %import common.WS
    %ignore WS
    %ignore COMMENT
    """,
    parser="lalr",
    transformer=TreeToOplist(),
)


def parse(text):
    """Parse a HERA program into a list of Op objects."""
    try:
        tree = _parser.parse(text)
    except UnexpectedCharacters as e:
        raise HERAError("unexpected character", e.line, e.column) from None
    except UnexpectedToken as e:
        if e.token.type == "$END":
            raise HERAError("unexpected end of file") from None
        else:
            raise HERAError("unexpected character", e.line, e.column) from None
    except LarkError as e:
        raise HERAError("invalid syntax", e.line, e.column) from None

    if isinstance(tree, Tree):
        return tree.children
    elif isinstance(tree, Op):
        return [tree]
    else:
        return tree


def replace_escapes(s):
    return re.sub(r"\\.", repl, s)


def repl(matchobj):
    c = matchobj.group(0)[1]
    if c == "n":
        return "\n"
    elif c == "t":
        return "\t"
    elif c == "\\":
        return "\\"
    elif c == '"':
        return '"'
    else:
        # TODO: Give a warning for this.
        return "\\" + c
