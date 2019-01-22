"""The expression mini-language for the debugger.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from collections import namedtuple


def parse(line):
    """Return a parse tree for the line of code. Raise a SyntaxError if it is not
    well-formatted.
    """
    return MiniParser(MiniLexer(line)).parse()


class MiniParser:
    """A parser for the debugger's expression mini-language.

      start := expr

      expr := mem | REGISTER | INT
      mem  := MEM LBRACKET expr RBRACKET
    """

    def __init__(self, lexer):
        self.lexer = lexer

    def parse(self):
        tree = self.match_expr()
        tkn = self.lexer.next_token()
        if tkn[0] == TOKEN_EOF:
            return tree
        else:
            raise SyntaxError("trailing input")

    def match_expr(self):
        tkn = self.lexer.next_token()
        if tkn[0] == TOKEN_MEM:
            self.assert_next(TOKEN_LBRACKET)
            address = self.match_expr()
            self.assert_next(TOKEN_RBRACKET)
            return MemoryNode(address)
        elif tkn[0] == TOKEN_INT:
            try:
                return IntNode(int(tkn[1], base=0))
            except ValueError:
                raise SyntaxError("invalid integer literal: {}".format(tkn[1]))
        elif tkn[0] == TOKEN_REGISTER:
            return RegisterNode(tkn[1])
        elif tkn[0] == TOKEN_SYMBOL:
            return SymbolNode(tkn[1])
        else:
            self.raise_unexpected(tkn)

    def assert_next(self, typ):
        tkn = self.lexer.next_token()
        if tkn[0] != typ:
            self.raise_unexpected(tkn)

    def raise_unexpected(self, tkn):
        if tkn[0] == TOKEN_EOF:
            raise SyntaxError("premature end of input")
        elif tkn[0] == TOKEN_UNKNOWN:
            raise SyntaxError("unrecognized input `{}`".format(tkn[1]))
        else:
            raise SyntaxError("did not expect `{}` in this position".format(tkn[1]))


MemoryNode = namedtuple("MemoryNode", ["address"])
RegisterNode = namedtuple("RegisterNode", ["value"])
IntNode = namedtuple("IntNode", ["value"])
SymbolNode = namedtuple("SymbolNode", ["value"])


class MiniLexer:
    """A lexer for the debugger's expression mini-language."""

    def __init__(self, text):
        self.text = text
        self.position = 0

    def next_token(self):
        # Skip whitespace.
        while self.position < len(self.text) and self.text[self.position].isspace():
            self.position += 1

        if self.position >= len(self.text):
            return TOKEN_EOF, ""

        ch = self.text[self.position]
        if ch in "mM":
            return self.advance_and_return(TOKEN_MEM)
        elif ch == "[":
            return self.advance_and_return(TOKEN_LBRACKET)
        elif ch == "]":
            return self.advance_and_return(TOKEN_RBRACKET)
        elif ch.isalpha() or ch == "_":
            length = self.read_register()
            if length != -1:
                return self.advance_and_return(TOKEN_REGISTER, length=length)
            else:
                length = self.read_symbol()
                return self.advance_and_return(TOKEN_SYMBOL, length=length)
        elif ch.isdigit():
            length = self.read_int()
            return self.advance_and_return(TOKEN_INT, length=length)
        elif ch == "-":
            self.position += 1
            length = self.read_int()
            self.position -= 1
            return self.advance_and_return(TOKEN_INT, length=length)
        else:
            return self.advance_and_return(TOKEN_UNKNOWN)

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
        length = 2
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


TOKEN_INT = "TOKEN_INT"
TOKEN_MEM = "TOKEN_MEM"
TOKEN_REGISTER = "TOKEN_REGISTER"
TOKEN_LBRACKET = "TOKEN_LBRACKET"
TOKEN_RBRACKET = "TOKEN_RBRACKET"
TOKEN_SYMBOL = "TOKEN_SYMBOL"
TOKEN_EOF = "TOKEN_EOF"
TOKEN_UNKNOWN = "TOKEN_UNKNOWN"
