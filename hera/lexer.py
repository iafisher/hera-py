from enum import Enum

from hera.data import Location, Token


class Lexer:
    """A lexer for HERA (and for the debugging mini-language)."""

    def __init__(self, text, *, path=None):
        self.text = text
        self.file_lines = text.splitlines()
        self.position = 0
        self.line = 1
        self.column = 1
        self.path = path or "<string>"
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
                length = self.read_register()
                if length != -1:
                    self.set_token(TOKEN.REGISTER, length=length)
                else:
                    length = self.read_symbol()
                    self.set_token(TOKEN.SYMBOL, length=length)
            elif ch.isdigit():
                length = self.read_int()
                self.set_token(TOKEN.INT, length=length)
            elif ch == ":":
                self.position += 1
                length = self.read_symbol()
                self.set_token(TOKEN.FMT, length=length)
            elif ch == "-":
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
            elif ch == ",":
                self.set_token(TOKEN.COMMA)
            else:
                self.set_token(TOKEN.UNKNOWN)

        return self.tkn

    def read_register(self):
        ch = self.text[self.position]
        if ch in "rR":
            if self.peek_char() in "tT":
                return 2
            elif self.peek_char().isdigit():
                length = 2
                while self.peek_char(length).isdigit():
                    length += 1
                return length
        elif ch in "pP":
            if self.text[self.position :].lower().startswith("pc_ret"):
                return 6
            elif self.text[self.position :].lower().startswith("pc"):
                return 2
        elif ch in "fF":
            if self.text[self.position :].lower().startswith("fp_alt"):
                return 6
            elif self.text[self.position :].lower().startswith("fp"):
                return 2
        elif ch in "sS":
            if self.peek_char() in "pP":
                return 2

        # Default: not a register.
        return -1

    def read_int(self):
        length = 1
        digits = set([str(i) for i in range(10)])
        peek = self.peek_char()
        if self.text[self.position] == "0" and peek and peek in "boxBOX":
            length = 2
            if self.peek_char() in "xX":
                digits |= set("abcdefABCDEF")

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


class TOKEN(Enum):
    # Values
    INT = "TOKEN_INT"
    REGISTER = "TOKEN_REGISTER"
    SYMBOL = "TOKEN_SYMBOL"
    STRING = "TOKEN_STRING"
    CHAR = "TOKEN_CHAR"

    # Operators
    MINUS = "TOKEN_MINUS"
    AT = "TOKEN_AT"
    ASTERISK = "TOKEN_ASTERISK"
    PLUS = "TOKEN_PLUS"
    SLASH = "TOKEN_SLASH"

    LPAREN = "TOKEN_LPAREN"
    RPAREN = "TOKEN_RPAREN"
    COMMA = "TOKEN_COMMA"

    FMT = "TOKEN_FMT"
    INCLUDE = "TOKEN_INCLUDE"
    EOF = "TOKEN_EOF"
    UNKNOWN = "TOKEN_UNKNOWN"
