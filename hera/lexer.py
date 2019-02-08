"""The lexer for HERA and the debugging mini-language.

Consumed by hera/parser.py and hera/debugger/miniparser.py.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import string
from typing import Optional

from hera.data import Location, Messages, Token
from hera.utils import NAMED_REGISTERS


class Lexer:
    """A lexer for HERA (and for the debugging mini-language)."""

    def __init__(self, text: str, *, path: Optional[str] = None) -> None:
        self.text = text
        self.file_lines = text.splitlines()
        if self.text.endswith("\n"):
            self.file_lines.append("")
        self.position = 0
        self.line = 1
        self.column = 1
        self.path = path or "<string>"
        self.messages = Messages()
        # Set the current token.
        self.next_token()

    def get_location(self) -> Location:
        return Location(self.line, self.column, self.path, self.file_lines)

    def next_token(self) -> Token:
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
                # TODO: This doesn't handle e.g. x-10.
                if self.peek_char().isdigit():
                    self.position += 1
                    length = self.read_int()
                    self.position -= 1
                    self.set_token(Token.INT, length=length + 1)
                else:
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
        length = 1
        while True:
            ch = self.peek_char(length)
            if not (ch.isalpha() or ch.isdigit() or ch == "_"):
                break
            length += 1
        return length

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
        sbuilder = []
        loc = self.get_location()
        self.next_char()
        while self.position < len(self.text) and self.text[self.position] != '"':
            if self.text[self.position] == "\\":
                if self.position == len(self.text) - 1:
                    self.next_char()
                    break

                escape = escape_char(self.text[self.position + 1])
                sbuilder.append(escape)
                self.next_char()
                if len(escape) == 2:
                    self.warn("unrecognized backslash escape", self.get_location())
                self.next_char()
            else:
                sbuilder.append(self.text[self.position])
                self.next_char()

        if self.position == len(self.text):
            self.tkn = Token(Token.ERROR, "unclosed string literal", loc)
            return

        self.next_char()
        s = "".join(sbuilder)
        self.tkn = Token(Token.STRING, s, loc)

    def consume_char(self) -> None:
        loc = self.get_location()
        self.next_char()
        start = self.position
        while self.position < len(self.text) and self.text[self.position] != "'":
            if self.text[self.position] == "\\":
                self.next_char()
            self.next_char()

        if self.position == len(self.text):
            self.tkn = Token(Token.ERROR, "unclosed character literal", loc)
            return

        contents = self.text[start : self.position]

        if len(contents) == 1:
            loc = loc._replace(column=loc.column + 1)
            self.tkn = Token(Token.CHAR, contents, loc)
        elif len(contents) == 2 and contents[0] == "\\":
            loc = loc._replace(column=loc.column + 2)
            escape = escape_char(contents[1])
            if len(escape) == 2:
                self.tkn = Token(Token.CHAR, escape[1], loc)
                self.warn("unrecognized backslash escape", loc)
            else:
                self.tkn = Token(Token.CHAR, escape, loc)
        else:
            self.tkn = Token(Token.ERROR, "over-long character literal", loc)

        self.next_char()

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
        if self.text[self.position] == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    def peek_char(self, n=1) -> str:
        return (
            self.text[self.position + n] if self.position + n < len(self.text) else ""
        )

    def set_token(self, typ: str, *, length=1) -> None:
        loc = self.get_location()
        value = self.text[self.position : self.position + length]
        for _ in range(length):
            self.next_char()
        self.tkn = Token(typ, value, loc)

    def err(self, msg: str, loc) -> None:
        self.messages.err(msg, loc)

    def warn(self, msg: str, loc) -> None:
        self.messages.warn(msg, loc)


def escape_char(c):
    """Return the special character that `c` encodes.

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


def is_register(s):
    return (s[0] in "rR" and s[1:].isdigit()) or s.lower() in NAMED_REGISTERS
