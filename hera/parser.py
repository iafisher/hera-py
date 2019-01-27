"""Parse HERA programs.

`parse` is the only function intended for public use.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
import os
import re
from typing import List, Set, Tuple

from lark import Lark, Token as LarkToken, Transformer
from lark.exceptions import LarkError, UnexpectedCharacters, UnexpectedToken

from .data import HERAError, IntToken, Location, Messages, Op, Token
from .stdlib import TIGER_STDLIB_STACK, TIGER_STDLIB_STACK_DATA
from .utils import is_register, read_file


def parse(text: str, *, path=None, visited=None) -> Tuple[List[Op], Messages]:
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
    if visited is None:
        visited = set()

    if path is not None:
        visited.add(get_canonical_path(path))

    file_lines = text.splitlines()
    base_location = Location(None, None, path or "<string>", file_lines)
    messages = Messages()

    try:
        tree = _parser.parse(text)
        ops = TreeToOplist(messages, base_location).transform(tree)
    except UnexpectedCharacters as e:
        loc = base_location._replace(line=e.line, column=e.column)
        return ([], Messages("unexpected character", loc))
    except UnexpectedToken as e:
        if e.token.type == "$END":
            return ([], Messages("unexpected end of input"))
        else:
            loc = base_location._replace(line=e.line, column=e.column)
            return ([], Messages("unexpected character", loc))
    except LarkError as e:
        loc = base_location._replace(line=e.line, column=e.column)
        return ([], Messages("invalid syntax", base_location))

    conversion_messages = convert_tokens(ops, base_location)
    # Don't need to check errors immediately, as none of them could be fatal.
    messages.extend(conversion_messages)

    # Expand #include statements.
    expanded_ops = []
    for op in ops:
        if op.name == "#include" and len(op.args) == 1:
            included_ops, include_messages = expand_include(op.args[0], path, visited)
            messages.extend(include_messages)
            expanded_ops.extend(included_ops)
        else:
            expanded_ops.append(op)
    return (expanded_ops, messages)


def convert_tokens(ops: List[Op], base_location: Location) -> Messages:
    """Convert all tokens in the list of ops from Lark Token objects to HERA Token and
    IntToken objects, tagged with `base_location`.
    """
    messages = Messages()
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
                if not arg.startswith("0o"):
                    messages.warn('consider using "0o" prefix for octal numbers', loc)
                try:
                    op.args[j] = IntToken(arg, loc, base=8)
                except ValueError:
                    # This is only necessary for octal because invalid digits for other
                    # bases are ruled out in the parser.
                    messages.err("invalid octal literal", loc)
            elif arg.type == "BINARY":
                op.args[j] = IntToken(arg, augment_location(base_location, arg), base=2)
            else:
                op.args[j] = Token(arg.type, arg, augment_location(base_location, arg))
        ops[i] = op._replace(name=name)
    return messages


def expand_include(
    include_path: str, root_path: str, visited: Set[str]
) -> Tuple[List[Op], Messages]:
    """Open the file named by `include_path` and return its parsed contents.

    `root_path` is the path of the including file, which is necessary for determining
    the correct base path, e.g. #include "lib.hera" in foo/main.hera resolves to
    foo/lib.hera, but #include "lib.hera" in bar/main.hera resolves to bar/lib.hera.
    """
    # `include_path` is generally a Token object so it can be passed as the `loc`
    # argument of `messages.err` and `messages.warn`.
    loc = include_path
    if include_path.startswith("<"):
        return expand_angle_include(include_path)
    else:
        # Strip off the leading and trailing quote.
        include_path = include_path[1:-1]
        if root_path is not None:
            include_path = os.path.join(os.path.dirname(root_path), include_path)

        if get_canonical_path(include_path) in visited:
            return ([], Messages("recursive include", loc))

        try:
            included_program = read_file(include_path)
        except HERAError as e:
            return ([], Messages(str(e), loc))

    return parse(included_program, path=include_path, visited=visited)


def expand_angle_include(include_path: str) -> Tuple[List[Op], Messages]:
    """Same as expand_include, except with `include_path` known to be an angle-bracket
    include, e.g.

      #include <system-library>

    rather than

      #include "user-library"

    The `include_path` string still has the angle brackets.
    """
    # There is no check for recursive includes in this function, under the assumption
    # that system libraries do not have recursive includes.
    loc = include_path
    if include_path == "<HERA.h>":
        return (
            [],
            Messages(
                "#include <HERA.h> is not necessary for hera-py", loc, warning=True
            ),
        )
    elif include_path == "<Tiger-stdlib-stack-data.hera>":
        included_program = TIGER_STDLIB_STACK_DATA
    elif include_path == "<Tiger-stdlib-stack.hera>":
        included_program = TIGER_STDLIB_STACK
    else:
        include_path = include_path[1:-1]
        root_path = os.environ.get("HERA_C_DIR", "/home/courses/lib/HERA-lib")
        try:
            included_program = read_file(os.path.join(root_path, include_path))
        except HERAError as e:
            return ([], Messages(str(e), loc))

    return parse(included_program, path=include_path)


class TreeToOplist(Transformer):
    """A class to transform Lark's parse tree into a list of HERA ops."""

    def __init__(self, messages, base_location, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = messages
        self.base_location = base_location

    def start(self, matches):
        if len(matches) == 2:
            return [matches[0]] + matches[1]
        else:
            return matches[0]

    def cpp_program(self, matches):
        self.messages.warn("void HERA_main() { ... } is not necessary for hera-py")
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
            loc = self.base_location._replace(line=line, column=column)

            # Disallow newlines.
            if "\n" in otkn:
                self.messages.err("string literals may not contain newlines", loc)

            try:
                s = replace_escapes(otkn[1:-1])
            except HERAError:
                self.messages.err("invalid backslash escape", loc)
                return otkn

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
                try:
                    c = char_to_escape(s[1])
                except HERAError:
                    c = "\0"
                    loc = self.base_location._replace(line=line, column=column + 2)
                    self.messages.err("invalid backslash escape", loc)
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
        raise HERAError("invalid backslash escape: " + c)


def get_canonical_path(fpath):
    if fpath == "-" or fpath == "<string>":
        return fpath
    else:
        return os.path.realpath(fpath)


def augment_location(base_location, token):
    """Add the line and column information from the token to the Location object."""
    return base_location._replace(line=token.line, column=token.column)
