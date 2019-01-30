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
    """A parser for the debugger's expression mini-language. Arithmetic operations have
    the usual precedence.

      start := FORMAT? exprlist

      exprlist := (expr COMMA)* expr

      expr := expr op expr | LPAREN expr RPAREN | MINUS expr | AT expr | atom
      op   := PLUS | MINUS | ASTERISK | SLASH
      atom := REGISTER | INT | SYMBOL

    Based on the Pratt parser from Thorsten Ball's "Writing an Interpreter in Go".
    https://interpreterbook.com/

    All match methods in this class expect that self.lexer.tkn is equal to the first
    token of the expression to be matched, and they leave self.lexer.tkn on the first
    token of the next expression.
    """

    def __init__(self, lexer):
        self.lexer = lexer

    def parse(self):
        self.lexer.next_token()
        tree = self.match_exprlist()
        if self.lexer.tkn[0] == TOKEN_EOF:
            return tree
        else:
            raise SyntaxError("trailing input")

    def match_exprlist(self):
        """Match a sequence of comma-separated expressions."""
        seq = []

        if self.lexer.tkn[0] == TOKEN_FMT:
            fmt = self.lexer.tkn[1]
            self.lexer.next_token()
        else:
            fmt = ""

        while True:
            expr = self.match_expr(PREC_LOWEST)
            seq.append(expr)
            if self.lexer.tkn[0] == TOKEN_COMMA:
                self.lexer.next_token()
            else:
                break

        return SeqNode(fmt, seq)

    def match_expr(self, precedence):
        """Parse the expression with the given precedence."""
        tkn = self.lexer.tkn
        if tkn[0] == TOKEN_AT:
            self.lexer.next_token()
            address = self.match_expr(PREC_PREFIX)
            left = MemoryNode(address)
        elif tkn[0] == TOKEN_INT:
            try:
                left = IntNode(int(tkn[1], base=0))
            except ValueError:
                raise SyntaxError("invalid integer literal: {}".format(tkn[1]))
            else:
                self.lexer.next_token()
        elif tkn[0] == TOKEN_MINUS:
            self.lexer.next_token()
            left = MinusNode(self.match_expr(PREC_PREFIX))
        elif tkn[0] == TOKEN_REGISTER:
            left = RegisterNode(tkn[1])
            self.lexer.next_token()
        elif tkn[0] == TOKEN_SYMBOL:
            left = SymbolNode(tkn[1])
            self.lexer.next_token()
        elif tkn[0] == TOKEN_LPAREN:
            self.lexer.next_token()
            left = self.match_expr(PREC_LOWEST)
            if self.lexer.tkn[0] != TOKEN_RPAREN:
                self.unexpected(self.lexer.tkn)
            self.lexer.next_token()
        else:
            self.unexpected(tkn)

        infix_tkn = self.lexer.tkn
        while infix_tkn[0] in PREC_MAP and precedence < PREC_MAP[infix_tkn[0]]:
            infix_precedence = PREC_MAP[infix_tkn[0]]
            self.lexer.next_token()
            right = self.match_expr(infix_precedence)
            if infix_tkn[0] == TOKEN_PLUS:
                left = AddNode(left, right)
            elif infix_tkn[0] == TOKEN_MINUS:
                left = SubNode(left, right)
            elif infix_tkn[0] == TOKEN_ASTERISK:
                left = MulNode(left, right)
            elif infix_tkn[0] == TOKEN_SLASH:
                left = DivNode(left, right)
            else:
                raise RuntimeError("unhandled infix operator in parser")
            infix_tkn = self.lexer.tkn
        return left

    def unexpected(self, tkn):
        if tkn[0] == TOKEN_EOF:
            raise SyntaxError("premature end of input")
        elif tkn[0] == TOKEN_UNKNOWN:
            raise SyntaxError("unrecognized input `{}`".format(tkn[1]))
        else:
            raise SyntaxError("did not expect `{}` in this position".format(tkn[1]))


SeqNode = namedtuple("SeqNode", ["fmt", "seq"])


class MemoryNode(namedtuple("MemoryNode", ["address"])):
    def __str__(self):
        return "@[{}]".format(self.address)


class RegisterNode(namedtuple("RegisterNode", ["value"])):
    def __str__(self):
        return self.value


class IntNode(namedtuple("IntNode", ["value"])):
    def __str__(self):
        return str(self.value)


class SymbolNode(namedtuple("SymbolNode", ["value"])):
    def __str__(self):
        return str(self.value)


class MinusNode(namedtuple("MinusNode", ["arg"])):
    def __str__(self):
        return "-({})".format(self.arg)


class AddNode(namedtuple("AddNode", ["left", "right"])):
    def __str__(self):
        return "({}) + ({})".format(self.left, self.right)


class SubNode(namedtuple("SubNode", ["left", "right"])):
    def __str__(self):
        return "({}) - ({})".format(self.left, self.right)


class MulNode(namedtuple("MulNode", ["left", "right"])):
    def __str__(self):
        return "({}) * ({})".format(self.left, self.right)


class DivNode(namedtuple("DivNode", ["left", "right"])):
    def __str__(self):
        return "({}) / ({})".format(self.left, self.right)


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
            return TOKEN_EOF, ""

        ch = self.text[self.position]
        if ch.isalpha() or ch == "_":
            length = self.read_register()
            if length != -1:
                return self.advance_and_return(TOKEN_REGISTER, length=length)
            else:
                length = self.read_symbol()
                return self.advance_and_return(TOKEN_SYMBOL, length=length)
        elif ch.isdigit():
            length = self.read_int()
            return self.advance_and_return(TOKEN_INT, length=length)
        elif ch == ":":
            self.position += 1
            length = self.read_symbol()
            return self.advance_and_return(TOKEN_FMT, length=length)
        elif ch == "-":
            return self.advance_and_return(TOKEN_MINUS)
        elif ch == "+":
            return self.advance_and_return(TOKEN_PLUS)
        elif ch == "/":
            return self.advance_and_return(TOKEN_SLASH)
        elif ch == "*":
            return self.advance_and_return(TOKEN_ASTERISK)
        elif ch == "@":
            return self.advance_and_return(TOKEN_AT)
        elif ch == "(":
            return self.advance_and_return(TOKEN_LPAREN)
        elif ch == ")":
            return self.advance_and_return(TOKEN_RPAREN)
        elif ch == ",":
            return self.advance_and_return(TOKEN_COMMA)
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


TOKEN_INT = "TOKEN_INT"
TOKEN_REGISTER = "TOKEN_REGISTER"
TOKEN_SYMBOL = "TOKEN_SYMBOL"
TOKEN_FMT = "TOKEN_FMT"
TOKEN_MINUS = "TOKEN_MINUS"
TOKEN_AT = "TOKEN_AT"
TOKEN_ASTERISK = "TOKEN_ASTERISK"
TOKEN_PLUS = "TOKEN_PLUS"
TOKEN_SLASH = "TOKEN_SLASH"
TOKEN_LPAREN = "TOKEN_LPAREN"
TOKEN_RPAREN = "TOKEN_RPAREN"
TOKEN_COMMA = "TOKEN_COMMA"
TOKEN_EOF = "TOKEN_EOF"
TOKEN_UNKNOWN = "TOKEN_UNKNOWN"


# Operator precedence
PREC_MAP = {TOKEN_PLUS: 1, TOKEN_MINUS: 1, TOKEN_SLASH: 2, TOKEN_ASTERISK: 2}
PREC_LOWEST = 0
PREC_PREFIX = 3
