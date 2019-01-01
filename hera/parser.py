"""Parse HERA programs.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: December 2018
"""
import os
import re
import sys
from collections import namedtuple

from lark import Lark, Token as LarkToken, Transformer, Tree
from lark.exceptions import LarkError, UnexpectedCharacters, UnexpectedToken

from . import config
from .data import IntToken, Location, Op, Token
from .utils import emit_error, emit_warning, get_canonical_path, is_register


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
        return Op(LarkToken("SYMBOL", "#include"), [matches[0]])

    def value(self, matches):
        line = matches[0].line
        column = matches[0].column

        if matches[0].type == "STRING":
            otkn = matches[0]
            s = replace_escapes(otkn[1:-1])
            ntkn = LarkToken("STRING", s)
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
                c = char_to_escape(s[1])
            else:
                c = s
            return LarkToken("CHAR", ord(c), line=line, column=column)
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


def parse(text, *, fpath=None, expand_includes=True, visited=None):
    """Parse a HERA program from a string into a list of Op objects.

    `fpath` is the path of the file being parsed, as it will appear in error and
    debugging messages. It defaults to "<string>".

    `expand_includes` determines whether an #include statement should be executed during
    parsing or not.

    `visited` is a set of file paths that have already been visited. If any #include
    statement matches a path in this set, an error is raised.
    """
    if visited is None:
        visited = set()

    if fpath is not None:
        visited.add(get_canonical_path(fpath))

    linevector = text.splitlines()
    base_location = Location(None, None, fpath or "<string>", linevector)

    try:
        tree = _parser.parse(text)
    except UnexpectedCharacters as e:
        loc = base_location._replace(line=e.line, column=e.column)
        emit_error("unexpected character", loc=loc, exit=True)
    except UnexpectedToken as e:
        if e.token.type == "$END":
            emit_error("unexpected end of file", exit=True)
        else:
            loc = base_location._replace(line=e.line, column=e.column)
            emit_error("unexpected character", loc=loc, exit=True)
    except LarkError as e:
        loc = base_location._replace(line=e.line, column=e.column)
        emit_error("invalid syntax", loc=base_location, exit=True)

    if isinstance(tree, Tree):
        ops = tree.children
    elif isinstance(tree, Op):
        ops = [tree]
    else:
        ops = tree

    convert_tokens(ops, base_location)

    if expand_includes:
        expanded_ops = []
        for op in ops:
            if op.name == "#include" and len(op.args) == 1:
                if op.args[0].startswith("<"):
                    # TODO: Probably need to handle these somehow.
                    continue

                # Strip off the leading and trailing quote.
                include_path = op.args[0][1:-1]
                include_path = os.path.join(os.path.dirname(fpath), include_path)

                if get_canonical_path(include_path) in visited:
                    # TODO: Do I _need_ to exit immediately here, or can I catch more
                    # errors?
                    emit_error("recursive include", loc=op.args[0].location, exit=True)

                expanded_ops.extend(parse_file(include_path, visited=visited))
            else:
                expanded_ops.append(op)
        ops = expanded_ops
    return ops


def parse_file(fpath, *, expand_includes=True, allow_stdin=False, visited=None):
    """Convenience function for parsing a HERA file. Reads the contents of the file and
    delegates parsing to the `parse` function.

    `allow_stdin` should be set to True if you wish the file path "-" to be interpreted
    as standard input instead of a file with that actual name. See `parse` for the
    meaning of `expand_includes` and `visited`.
    """
    if allow_stdin and fpath == "-":
        try:
            program = sys.stdin.read()
        except (IOError, KeyboardInterrupt):
            print()
            sys.exit(3)
    else:
        try:
            with open(fpath) as f:
                program = f.read()
        except FileNotFoundError:
            emit_error('file "{}" does not exist.'.format(fpath), exit=True)
        except PermissionError:
            emit_error('permission denied to open file "{}".'.format(fpath), exit=True)
        except OSError:
            emit_error('could not open file "{}".'.format(fpath), exit=True)

    return parse(program, fpath=fpath, expand_includes=expand_includes, visited=visited)


def convert_tokens(ops, base_location):
    for i, op in enumerate(ops):
        name = Token(op.name.type, op.name, augment_location(base_location, op.name))
        for j, arg in enumerate(op.args):
            if arg.type == "DECIMAL" or arg.type == "CHAR":
                op.args[j] = IntToken(arg, augment_location(base_location, arg))
            elif arg.type == "HEX":
                op.args[j] = IntToken(
                    arg, augment_location(base_location, arg), base=16
                )
            elif arg.type == "OCTAL":
                if not arg.startswith("0o"):
                    msg = "zero-prefixed numbers are interpreted as octal"
                    msg += " (consider using 0o prefix instead)"
                    loc = augment_location(base_location, arg)
                    emit_warning(msg, loc=loc),
                op.args[j] = IntToken(arg, augment_location(base_location, arg), base=8)
            elif arg.type == "BINARY":
                op.args[j] = IntToken(arg, augment_location(base_location, arg), base=2)
            else:
                op.args[j] = Token(arg.type, arg, augment_location(base_location, arg))
        ops[i] = op._replace(name=name)


def augment_location(base_location, token):
    return base_location._replace(line=token.line, column=token.column)


def replace_escapes(s):
    return re.sub(r"\\.", lambda m: char_to_escape(m.group(0)[1]), s)


def char_to_escape(c):
    """Return the special character that `c` encodes.

        >>> char_to_escape("n")
        "\n"
    """
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
