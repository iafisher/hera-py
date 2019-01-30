from enum import Enum


class MiniLexer:
    """A lexer for the debugger's expression mini-language."""

    def __init__(self, text):
        self.text = text
        self.tkn = None
        self.position = 0

    def next_token(self):
        self.tkn = self.next_token_helper()
        return self.tkn

    def next_token_helper(self):
        # Skip whitespace.
        while self.position < len(self.text) and self.text[self.position].isspace():
            self.position += 1

        if self.position >= len(self.text):
            return Token.EOF, ""

        ch = self.text[self.position]
        if ch.isalpha() or ch == "_":
            length = self.read_register()
            if length != -1:
                return self.advance_and_return(Token.REGISTER, length=length)
            else:
                length = self.read_symbol()
                return self.advance_and_return(Token.SYMBOL, length=length)
        elif ch.isdigit():
            length = self.read_int()
            return self.advance_and_return(Token.INT, length=length)
        elif ch == ":":
            self.position += 1
            length = self.read_symbol()
            return self.advance_and_return(Token.FMT, length=length)
        elif ch == "-":
            return self.advance_and_return(Token.MINUS)
        elif ch == "+":
            return self.advance_and_return(Token.PLUS)
        elif ch == "/":
            return self.advance_and_return(Token.SLASH)
        elif ch == "*":
            return self.advance_and_return(Token.ASTERISK)
        elif ch == "@":
            return self.advance_and_return(Token.AT)
        elif ch == "(":
            return self.advance_and_return(Token.LPAREN)
        elif ch == ")":
            return self.advance_and_return(Token.RPAREN)
        elif ch == ",":
            return self.advance_and_return(Token.COMMA)
        else:
            return self.advance_and_return(Token.UNKNOWN)

    def read_register(self):
        ch = self.text[self.position]
        if ch in "rR":
            if self.peek() in "tT":
                return 2
            elif self.peek().isdigit():
                length = 2
                while self.peek(length).isdigit():
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
            if self.peek() in "pP":
                return 2

        # Default: not a register.
        return -1

    def read_int(self):
        length = 1
        digits = set([str(i) for i in range(10)])
        if self.text[self.position] == "0" and self.peek() in "boxBOX":
            length = 2
            if self.peek() in "xX":
                digits |= set("abcdefABCDEF")

        while self.peek(length) in digits:
            length += 1

        return length

    def read_symbol(self):
        length = 1
        while True:
            ch = self.peek(length)
            if not (ch.isalpha() or ch.isdigit() or ch == "_"):
                break
            length += 1
        return length

    def peek(self, n=1):
        return (
            self.text[self.position + n] if self.position + n < len(self.text) else ""
        )

    def advance_and_return(self, typ, *, length=1):
        start = self.position
        self.position += length
        return typ, self.text[start : start + length]


class Token(Enum):
    INT = "TOKEN_INT"
    REGISTER = "TOKEN_REGISTER"
    SYMBOL = "TOKEN_SYMBOL"
    FMT = "TOKEN_FMT"
    MINUS = "TOKEN_MINUS"
    AT = "TOKEN_AT"
    ASTERISK = "TOKEN_ASTERISK"
    PLUS = "TOKEN_PLUS"
    SLASH = "TOKEN_SLASH"
    LPAREN = "TOKEN_LPAREN"
    RPAREN = "TOKEN_RPAREN"
    COMMA = "TOKEN_COMMA"
    EOF = "TOKEN_EOF"
    UNKNOWN = "TOKEN_UNKNOWN"
