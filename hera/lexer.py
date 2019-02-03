"""The lexer for HERA and the debugging mini-language.

Consumed by hera/parser.py and hera/debugger/miniparser.py.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: February 2019
"""
import string

from hera.data import HERAError, Location, Messages, Token, TOKEN
from hera.utils import NAMED_REGISTERS


class Lexer:
    """A lexer for HERA (and for the debugging mini-language)."""

    def __init__(self, text, *, path=None):
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

    def get_location(self):
        return Location(self.line, self.column, self.path, self.file_lines)

    def next_token(self):
        self.skip()

        if self.position >= len(self.text):
            self.set_token(TOKEN.EOF, length=0)
        else:
            ch = self.text[self.position]
            if ch.isalpha() or ch == "_":
                length = self.read_symbol()
                if is_register(self.text[self.position : self.position + length]):
                    self.set_token(TOKEN.REGISTER, length=length)
                else:
                    self.set_token(TOKEN.SYMBOL, length=length)
            elif ch.isdigit():
                length = self.read_int()
                self.set_token(TOKEN.INT, length=length)
            elif ch == '"':
                loc = self.get_location()
                s = self.consume_str()
                self.tkn = Token(TOKEN.STRING, s, loc)
            elif ch == "'":
                if self.peek_char() == "\\":
                    if self.peek_char(3) == "'":
                        ch = self.peek_char(2)
                        escape = escape_char(ch)
                        self.next_char()  # open quote
                        self.next_char()  # backslash
                        loc = self.get_location()
                        self.next_char()  # character
                        self.next_char()  # end quote
                        if len(escape) == 2:
                            self.tkn = Token(TOKEN.CHAR, escape[1], loc)
                            self.warn("unrecognized backslash escape", loc)
                        else:
                            self.tkn = Token(TOKEN.CHAR, escape, loc)
                else:
                    if self.peek_char(2) == "'":
                        ch = self.peek_char()
                        self.next_char()  # open quote
                        loc = self.get_location()
                        self.next_char()  # character
                        self.next_char()  # end quote
                        self.tkn = Token(TOKEN.CHAR, ch, loc)
                    else:
                        self.set_token(TOKEN.UNKNOWN)
            elif self.text[self.position :].startswith("#include"):
                self.set_token(TOKEN.INCLUDE, length=len("#include"))
            elif ch == "<":
                self.next_char()
                length = self.read_bracketed()
                self.set_token(TOKEN.BRACKETED, length=length)
                if self.position < len(self.text):
                    self.next_char()
            elif ch == ":":
                self.position += 1
                length = self.read_symbol()
                self.set_token(TOKEN.FMT, length=length)
            elif ch == "-":
                if self.peek_char().isdigit():
                    self.position += 1
                    length = self.read_int()
                    self.position -= 1
                    self.set_token(TOKEN.INT, length=length + 1)
                else:
                    self.set_token(TOKEN.MINUS)
            elif ch == "+":
                self.set_token(TOKEN.PLUS)
            elif ch == "/":
                self.set_token(TOKEN.SLASH)
            elif ch == "*":
                self.set_token(TOKEN.ASTERISK)
            elif ch == "@":
                self.set_token(TOKEN.AT)
            elif ch == "(":
                self.set_token(TOKEN.LPAREN)
            elif ch == ")":
                self.set_token(TOKEN.RPAREN)
            elif ch == "{":
                self.set_token(TOKEN.LBRACE)
            elif ch == "}":
                self.set_token(TOKEN.RBRACE)
            elif ch == ",":
                self.set_token(TOKEN.COMMA)
            elif ch == ";":
                self.set_token(TOKEN.SEMICOLON)
            else:
                self.set_token(TOKEN.UNKNOWN)

        return self.tkn

    def read_int(self):
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

    def read_symbol(self):
        length = 1
        while True:
            ch = self.peek_char(length)
            if not (ch.isalpha() or ch.isdigit() or ch == "_"):
                break
            length += 1
        return length

    def read_bracketed(self):
        length = 1
        while self.position + length < len(self.text) and self.peek_char(length) != ">":
            length += 1
        if self.position + length == len(self.text):
            raise HERAError("unclosed bracketed expression", self.get_location())
        return length

    def consume_str(self):
        sbuilder = []
        loc = self.get_location()
        self.next_char()
        while self.position < len(self.text) and self.text[self.position] != '"':
            if self.text[self.position] == "\\":
                if self.position == len(self.text) - 1:
                    raise HERAError("unclosed string literal", loc)

                escape = escape_char(self.text[self.position + 1])
                sbuilder.append(escape)
                self.next_char()
                if len(escape) == 2:
                    self.warn("unrecognized backslash escape", self.get_location())
                self.next_char()
            else:
                sbuilder.append(self.text[self.position])
                self.next_char()
        if self.position < len(self.text):
            self.next_char()
        else:
            raise HERAError("unclosed string literal", loc)
        return "".join(sbuilder)

    def skip(self):
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

    def next_char(self):
        if self.text[self.position] == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    def peek_char(self, n=1):
        return (
            self.text[self.position + n] if self.position + n < len(self.text) else ""
        )

    def set_token(self, typ, *, length=1):
        loc = self.get_location()
        value = self.text[self.position : self.position + length]
        for _ in range(length):
            self.next_char()
        self.tkn = Token(typ, value, loc)

    def err(self, msg, loc):
        self.messages.err(msg, loc)

    def warn(self, msg, loc):
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
