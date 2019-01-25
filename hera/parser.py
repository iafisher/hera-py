"""Parse HERA programs.

`parse` is the only function intended for public use.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import os
import re
from typing import List

from lark import Lark, Token as LarkToken, Transformer, Tree
from lark.exceptions import LarkError, UnexpectedCharacters, UnexpectedToken

from .data import HERAError, IntToken, Location, Op, State, Token
from .utils import get_canonical_path, is_register, read_file


def parse(text: str, *, path=None, includes=True, state=State()) -> List[Op]:
    """Parse a HERA program.

    `path` is the path of the file being parsed, as it will appear in error and
    debugging messages. It defaults to "<string>".

    `includes` determines what happens when an #include statement is encountered. If
    `includes` is True, then the #include statement is interpreted as it is by the C
    preprocessor, i.e. the file identified by #include's argument is read, parsed, and
    pasted in with the rest of the operations. If it is False, then the #include
    statement is retained as an Op object.

    `visited` is a set of file paths that have already been visited, to prevent infinite
    regress if two files include each other directly or indirectly.
    """
    if path is not None:
        state.visited.add(get_canonical_path(path))

    file_lines = text.splitlines()
    base_location = Location(None, None, path or "<string>", file_lines)

    try:
        tree = _parser.parse(text)
        tree = TreeToOplist(state).transform(tree)
    except UnexpectedCharacters as e:
        loc = base_location._replace(line=e.line, column=e.column)
        state.error("unexpected character", loc=loc)
        return []
    except UnexpectedToken as e:
        if e.token.type == "$END":
            state.error("unexpected end of input")
        else:
            loc = base_location._replace(line=e.line, column=e.column)
            state.error("unexpected character", loc=loc)
        return []
    except LarkError as e:
        loc = base_location._replace(line=e.line, column=e.column)
        state.error("invalid syntax", loc=base_location)
        return []

    if isinstance(tree, Tree):
        ops = tree.children
    elif isinstance(tree, Op):
        ops = [tree]
    else:
        ops = tree

    convert_tokens(ops, base_location, state)

    if includes:
        ops = expand_includes(ops, path, state)

    return ops


def convert_tokens(ops: List[Op], base_location: Location, state=State()) -> None:
    """Convert all tokens in the list of ops from Lark Token objects to HERA Token and
    IntToken objects, tagged with `base_location`.
    """
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
                loc = augment_location(base_location, arg)
                if not arg.startswith("0o") and not state.warned_for_octal:
                    state.warning(
                        'consider using "0o" prefix for octal numbers', loc=loc
                    )
                    state.warned_for_octal = True
                try:
                    op.args[j] = IntToken(arg, loc, base=8)
                except ValueError:
                    # This is only necessary for octal because invalid digits for other
                    # bases are ruled out in the parser.
                    state.error("invalid octal literal", loc=loc)
            elif arg.type == "BINARY":
                op.args[j] = IntToken(arg, augment_location(base_location, arg), base=2)
            else:
                op.args[j] = Token(arg.type, arg, augment_location(base_location, arg))
        ops[i] = op._replace(name=name)


def expand_includes(ops: List[Op], path: str, state=State()) -> List[Op]:
    """Scan the list of ops and replace any #include "foo.hera" statement with the
    parsed contents of foo.hera.

    `path` is the path of the including file, which is necessary for determining the
    correct base path, e.g. #include "lib.hera" in foo/main.hera resolves to
    foo/lib.hera, but #include "lib.hera" in bar/main.hera resolves to bar/lib.hera.

    `visited` is the set of file paths that have already been visited.
    """
    expanded_ops = []
    for op in ops:
        if op.name == "#include" and len(op.args) == 1:
            if op.args[0].startswith("<"):
                # TODO: Probably need to handle these somehow.
                continue

            # Strip off the leading and trailing quote.
            include_path = op.args[0][1:-1]
            if path is not None:
                include_path = os.path.join(os.path.dirname(path), include_path)

            if get_canonical_path(include_path) in state.visited:
                state.error("recursive include", loc=op.args[0])
                continue

            try:
                included_program = read_file(include_path)
            except HERAError as e:
                state.error(str(e), loc=op.args[0])
                continue

            included_ops = parse(included_program, path=include_path, state=state)
            expanded_ops.extend(included_ops)
        else:
            expanded_ops.append(op)
    return expanded_ops


class TreeToOplist(Transformer):
    """Transform Lark's parse tree into a list of HERA ops."""

    def __init__(self, state, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = state

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
        self.state.warning("void HERA_main() { ... } is not necessary")
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
)


def augment_location(base_location, token):
    """Add the line and column information from the token to the Location object."""
    return base_location._replace(line=token.line, column=token.column)


def replace_escapes(s):
    """Replace all backslash escape sequences in the string with the special characters
    that they encode.
    """
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
