"""Parse HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
import os
import re
import sys
from collections import namedtuple

from lark import Lark, Token, Transformer, Tree
from lark.exceptions import LarkError, UnexpectedCharacters, UnexpectedToken

from . import config
from .utils import emit_warning, get_canonical_path, HERAError, IntToken, is_register


class Op(namedtuple("Op", ["name", "args", "location"])):
    def __new__(cls, name, args, location=None):
        return tuple.__new__(cls, (name, args, location))

    def __eq__(self, other):
        return (
            isinstance(other, Op)
            and self.name == other.name
            and self.args == other.args
        )


Location = namedtuple("Location", ["path", "lines"])


class TreeToOplist(Transformer):
    """Transform Lark's parse tree into a list of HERA ops."""

    def start(self, matches):
        # TODO: Figure out why all this is necessary.
        if len(matches) == 2:
            if isinstance(matches[0], tuple):
                return [matches[0]] + matches[1]
            else:
                return matches[0] + matches[1]
        elif len(matches) > 2:
            return matches[:-1] + matches[-1]
        else:
            return matches[0]

    def cpp_program(self, matches):
        emit_warning("void HERA_main() { ... } is not necessary")
        return matches

    def hera_program(self, matches):
        return matches

    def op(self, matches):
        return Op(matches[0], matches[1:])

    def include(self, matches):
        return Op("#include", [matches[0]])

    def value(self, matches):
        line = matches[0].line
        column = matches[0].column

        if matches[0].type == "DECIMAL":
            return IntToken(matches[0], line=line, column=column)
        elif matches[0].type == "HEX":
            return IntToken(matches[0], base=16, line=line, column=column)
        elif matches[0].type == "OCTAL":
            if not matches[0].startswith("0o"):
                msg = "zero-prefixed numbers are interpreted as octal"
                msg += " (consider using 0o prefix instead)"
                emit_warning(msg, line=matches[0].line, column=matches[0].column)
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
        elif matches[0].type == "CHAR":
            # Strip the leading and trailing quote.
            s = matches[0][1:-1]
            if s.startswith("\\"):
                c = replace_one_escape(s[1])
            else:
                c = s
            return IntToken(ord(c), line=line, column=column)
        elif matches[0].type == "SYMBOL":
            if is_register(matches[0]):
                matches[0].type = "REGISTER"
            return matches[0]
        else:
            return matches[0]


_parser = Lark(
    r"""
    start: include* (cpp_program | hera_program)

    cpp_program: _cpp_open (op | include)* _CPP_CLOSE
    hera_program: op (op | include)* |

    // Underscores before everything so that no tokens end up in the tree.
    _cpp_open: "void" _SYMBOL "(" ")" "{"
    _CPP_CLOSE: "}"
    _SYMBOL: SYMBOL

    include: "#include" ( STRING | /<[^>]+>/ )

    op: SYMBOL "(" _arglist? ")" ";"?

    _arglist: ( value "," )* value

    value: DECIMAL | HEX | OCTAL | BINARY | SYMBOL | STRING | CHAR

    SYMBOL: /[A-Za-z_][A-Za-z0-9_]*/
    DECIMAL: /-?[1-9][0-9]*/ | "0"
    HEX.2: /-?0x[0-9a-fA-F]+/
    OCTAL.2: /-?0o[0-7]+/ | /-?0[1-9]+/
    BINARY.2: /-?0b[01]+/
    STRING: /"(\\.|[^"])*"/
    CHAR: /'(\\.|.)'/

    COMMENT: ( "//" /[^\n]*/ | "/*" /([^*]|\*[^\/])*/ "*/" )

    %import common.WS
    %ignore WS
    %ignore COMMENT
    """,
    parser="lalr",
    transformer=TreeToOplist(),
)


def parse(text, *, expand_includes=False):
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


def parse_file(fpath, *, expand_includes=True, allow_stdin=False):
    """Parse a file containing a HERA program into a list of Op objects."""
    if allow_stdin and fpath == "-":
        # TODO: If I put #include "-" in a HERA file, this will go badly.
        program = sys.stdin.read()
    else:
        with open(fpath) as f:
            program = f.read()

    canonical_path = get_canonical_path(fpath)
    linevector = program.splitlines()
    loc = Location(fpath, linevector)

    try:
        ops = parse(program)
    except HERAError as e:
        e.location = loc
        raise e

    ops = [op._replace(location=loc) for op in ops]

    if expand_includes:
        expanded_ops = []
        for op in ops:
            if (
                op.name == "#include"
                and len(op.args) == 1
                and not op.args[0].startswith("<")
            ):
                # Strip off the leading and trailing quote.
                include_path = op.args[0][1:-1]
                include_path = os.path.join(os.path.dirname(fpath), include_path)
                expanded_ops.extend(parse_file(include_path))
            else:
                expanded_ops.append(op)
        return expanded_ops
    else:
        return ops


def replace_escapes(s):
    return re.sub(r"\\.", repl, s)


def repl(matchobj):
    c = matchobj.group(0)[1]
    return replace_one_escape(c)


def replace_one_escape(c):
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
