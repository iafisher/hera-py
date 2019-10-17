"""
The lexer for HERA and the debugging mini-language.

Consumed by hera/parser.py and hera/debugger/miniparser.py.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import string

from hera.data import Location, Messages, Token
from hera.utils import is_register, PATH_STRING


class Lexer:
    """A lexer for HERA (and for the debugging mini-language)."""

    def __init__(self, text: str, *, path: "Optional[str]" = PATH_STRING) -> None:
        self.text = text
        self.file_lines = text.splitlines()
        if self.text.endswith("\n"):
            self.file_lines.append("")
        self.position = 0
        self.line = 1
        self.column = 1
        self.path = path
        self.messages = Messages()
        # Set the current token.
        self.next_token()

    def get_location(self) -> Location:
        """Return the current location of the lexer."""
        return Location(self.line, self.column, self.path, self.file_lines)

    def next_token(self) -> Token:
        """Advance forward one token, set self.tkn to it, and return it."""
        self.skip()

        if self.position >= len(self.text):
            self.set_token(Token.EOF, length=0)
        else:
            ch = self.text[self.position]
            if ch.isalpha() or ch == "_":
                length = self.read_symbol()
                if is_register(self.text[self.position : self.position + length]):
                    self.set_token(Token.REGISTER, length=length)
                else:
                    self.set_token(Token.SYMBOL, length=length)
            elif ch.isdigit():
                length = self.read_int()
                self.set_token(Token.INT, length=length)
            elif ch == '"':
                self.consume_str()
            elif ch == "'":
                self.consume_char()
            elif self.text[self.position :].startswith("#include"):
                self.set_token(Token.INCLUDE, length=len("#include"))
            elif ch == "<":
                self.consume_bracketed()
            elif ch == ":":
                self.position += 1
                length = self.read_symbol()
                self.set_token(Token.FMT, length=length)
            elif ch == "-":
                self.set_token(Token.MINUS)
            elif ch == "+":
                self.set_token(Token.PLUS)
            elif ch == "/":
                self.set_token(Token.SLASH)
            elif ch == "*":
                self.set_token(Token.ASTERISK)
            elif ch == "@":
                self.set_token(Token.AT)
            elif ch == "(":
                self.set_token(Token.LPAREN)
            elif ch == ")":
                self.set_token(Token.RPAREN)
            elif ch == "{":
                self.set_token(Token.LBRACE)
            elif ch == "}":
                self.set_token(Token.RBRACE)
            elif ch == ",":
                self.set_token(Token.COMMA)
            elif ch == ";":
                self.set_token(Token.SEMICOLON)
            else:
                self.set_token(Token.UNKNOWN)

        return self.tkn

    def read_int(self) -> int:
        """Read an integer starting at the current position, and return its length."""
        length = 1
        digits = {str(i) for i in range(10)}
        peek = self.peek_char()
        if self.text[self.position] == "0" and peek and peek in "boxBOX":
            length = 2
            if self.peek_char() in "xX":
                digits |= set(string.ascii_letters)

        while self.peek_char(length) in digits:
            length += 1

        return length

    def read_symbol(self) -> int:
        """Read a symbol starting at the current position, and return its length."""
        length = 1
        while True:
            ch = self.peek_char(length)
            if not (ch.isalpha() or ch.isdigit() or ch == "_"):
                break
            length += 1
        return length

    HEX_DIGITS = "0123456789abcdefABCDEF"

    def read_escape_char(self) -> "Tuple[str, int]":
        """
        Read an escape sequence (assuming `self.text[self.position] == "\\"`) and return
        a pair (value, length), where `value` is what the escape sequence resolves to
        and `length` is the number of characters read.
        """
        peek = self.peek_char()
        loc = self.get_location()
        loc = loc._replace(column=loc.column + 1)
        if peek == "":
            return ("", 0)
        elif peek == "x":
            # Hex escapes
            peek2 = self.peek_char(2)
            peek3 = self.peek_char(3)
            if peek2 in self.HEX_DIGITS and peek3 in self.HEX_DIGITS:
                ordv = int(peek2 + peek3, base=16)
                return (chr(ordv), 3)
            else:
                self.warn("invalid hex escape", loc)
                return ("x", 1)
        elif peek.isdigit():
            # Octal escapes
            length = 1
            while length <= 3:
                if not self.peek_char(length).isdigit():
                    break
                length += 1

            val = self.text[self.position + 1 : self.position + length]

            try:
                ordv = int(val, base=8)
            except ValueError:
                self.warn("invalid octal escape", loc)
                return (self.peek_char(), 1)
            else:
                return (chr(ordv), length - 1)
        else:
            escape = escape_char(peek)
            if len(escape) == 2:
                self.warn("unrecognized backslash escape", loc)
            return (escape, 1)

    def consume_bracketed(self) -> None:
        self.next_char()
        loc = self.get_location()
        start = self.position
        while self.position < len(self.text) and self.text[self.position] != ">":
            self.next_char()

        if self.position == len(self.text):
            self.tkn = Token(Token.ERROR, "unclosed bracketed expression", loc)
            return

        self.tkn = Token(Token.BRACKETED, self.text[start : self.position], loc)
        self.next_char()

    def consume_str(self) -> None:
        """
        Advance the lexer to one past the end of a string literal starting at the
        current position, and set self.tkn appropriately.
        """
        loc = self.get_location()
        self.next_char()
        s = self.consume_delimited('"')

        if self.position == len(self.text):
            self.tkn = Token(Token.ERROR, "unclosed string literal", loc)
            return

        self.next_char()
        self.tkn = Token(Token.STRING, s, loc)

    def consume_char(self) -> None:
        """
        Advance the lexer to one past the end of a character literal starting at the
        current position, and set self.tkn appropriately.
        """
        loc = self.get_location()
        self.next_char()
        s = self.consume_delimited("'")

        if self.position == len(self.text):
            self.tkn = Token(Token.ERROR, "unclosed character literal", loc)
            return

        self.next_char()

        if len(s) == 1:
            self.tkn = Token(Token.CHAR, s, loc)
        elif len(s) == 2 and s[0] == "\\":
            self.tkn = Token(Token.CHAR, s[1], loc)
        else:
            self.tkn = Token(Token.ERROR, "over-long character literal", loc)

    def consume_delimited(self, delimiter: str) -> str:
        """
        Advance the lexer to one past the end of an expression delimited by the
        character `delimiter`, and set self.tkn appropriately.

        Backslash escapes inside the expression are converted, and escaped delimiters
        are ignored.

        This method exists to capture the shared functionality of consuming string and
        character literals.
        """
        sbuilder = []
        while self.position < len(self.text) and self.text[self.position] != delimiter:
            if self.text[self.position] == "\\":
                value, length = self.read_escape_char()
                self.next_char()
                if length == 0:
                    # Length of zero indicates EOF.
                    break

                sbuilder.append(value)
                for _ in range(length):
                    self.next_char()
            else:
                sbuilder.append(self.text[self.position])
                self.next_char()

        return "".join(sbuilder)

    def skip(self) -> None:
        """Skip past whitespace and comments."""
        while True:
            # Skip whitespace.
            while self.position < len(self.text) and self.text[self.position].isspace():
                self.next_char()

            # Skip comments.
            if self.position < len(self.text) and self.text[self.position] == "/":
                if self.peek_char() == "/":
                    while self.position < len(self.text):
                        if self.text[self.position] == "\n":
                            break
                        self.next_char()
                elif self.peek_char() == "*":
                    # Move past the "/*" at the start of the comment.
                    self.next_char()
                    self.next_char()
                    while self.position < len(self.text):
                        if self.text[self.position] == "*" and self.peek_char() == "/":
                            break
                        self.next_char()
                    # Skip the "*/" at the end of the comment.
                    self.next_char()
                    self.next_char()
                else:
                    break
            else:
                break

    def next_char(self) -> None:
        """
        Advance the position in the text by one. Do not call this method if the current
        position is past the end of the text.
        """
        if self.text[self.position] == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    def peek_char(self, n=1) -> str:
        """
        Return the n'th character in the text past the current position. If past the
        end, return the empty string.
        """
        return (
            self.text[self.position + n] if self.position + n < len(self.text) else ""
        )

    def set_token(self, typ: str, *, length=1) -> None:
        """
        Set self.tkn to a Token object whose type is `typ` and whose value is the
        substring of the input of length `length` starting at the current position. The
        lexer's position is advanced to one past the end of the token.
        """
        loc = self.get_location()
        value = self.text[self.position : self.position + length]
        for _ in range(length):
            self.next_char()
        self.tkn = Token(typ, value, loc)

    def warn(self, msg: str, loc) -> None:
        self.messages.warn(msg, loc)


def escape_char(c):
    """
    Return the special character that `c` encodes.

        >>> escape_char("n")
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
        return "\\" + c
