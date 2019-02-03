"""The expression mini-language for the debugger.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from collections import namedtuple

from ..lexer import Lexer, TOKEN
from ..data import HERAError
from ..utils import register_to_index


def parse(line):
    """Return a parse tree for the line of code. Raise a SyntaxError if it is not
    well-formatted.
    """
    return MiniParser(Lexer(line)).parse()


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
        tree = self.match_exprlist()
        if self.lexer.tkn.type == TOKEN.EOF:
            return tree
        else:
            raise SyntaxError("trailing input")

    def match_exprlist(self):
        """Match a sequence of comma-separated expressions."""
        seq = []

        if self.lexer.tkn.type == TOKEN.FMT:
            fmt = self.lexer.tkn.value
            self.lexer.next_token()
        else:
            fmt = ""

        while True:
            expr = self.match_expr(PREC_LOWEST)
            seq.append(expr)
            if self.lexer.tkn.type == TOKEN.COMMA:
                self.lexer.next_token()
            else:
                break

        return SeqNode(fmt, seq)

    def match_expr(self, precedence):
        """Parse the expression with the given precedence."""
        tkn = self.lexer.tkn
        if tkn.type == TOKEN.AT:
            self.lexer.next_token()
            address = self.match_expr(PREC_PREFIX)
            left = MemoryNode(address)
        elif tkn.type == TOKEN.INT:
            try:
                left = IntNode(int(tkn.value, base=0))
            except ValueError:
                raise SyntaxError("invalid integer literal: {}".format(tkn))
            else:
                self.lexer.next_token()
        elif tkn.type == TOKEN.MINUS:
            self.lexer.next_token()
            left = PrefixNode("-", self.match_expr(PREC_PREFIX))
        elif tkn.type == TOKEN.REGISTER:
            try:
                left = RegisterNode(register_to_index(tkn.value))
            except HERAError:
                raise SyntaxError("{} is not a valid register".format(tkn.value))
            self.lexer.next_token()
        elif tkn.type == TOKEN.SYMBOL:
            left = SymbolNode(tkn.value)
            self.lexer.next_token()
        elif tkn.type == TOKEN.LPAREN:
            self.lexer.next_token()
            left = self.match_expr(PREC_LOWEST)
            if self.lexer.tkn.type != TOKEN.RPAREN:
                self.unexpected(self.lexer.tkn)
            self.lexer.next_token()
        else:
            self.unexpected(tkn)

        infix_tkn = self.lexer.tkn
        while infix_tkn.type in PREC_MAP and precedence < PREC_MAP[infix_tkn.type]:
            infix_precedence = PREC_MAP[infix_tkn.type]
            self.lexer.next_token()
            right = self.match_expr(infix_precedence)
            left = InfixNode(infix_tkn.value, left, right)
            infix_tkn = self.lexer.tkn
        return left

    def unexpected(self, tkn):
        if tkn.type == TOKEN.EOF:
            raise SyntaxError("premature end of input")
        elif tkn.type == TOKEN.UNKNOWN:
            raise SyntaxError("unrecognized input `{}`".format(tkn))
        else:
            raise SyntaxError("did not expect `{}` in this position".format(tkn))


class SeqNode(namedtuple("SeqNode", ["fmt", "seq"])):
    def __str__(self):
        seqstr = ", ".join(map(str, self.seq))
        if self.fmt:
            return ":{} {}".format(self.fmt, seqstr)
        else:
            return seqstr


class MemoryNode(namedtuple("MemoryNode", ["address"])):
    def __str__(self):
        return "@{}".format(wrap(self.address))


class RegisterNode(namedtuple("RegisterNode", ["value"])):
    def __str__(self):
        return "R" + str(self.value)


class IntNode(namedtuple("IntNode", ["value"])):
    def __str__(self):
        return str(self.value)


class SymbolNode(namedtuple("SymbolNode", ["value"])):
    def __str__(self):
        return self.value


class PrefixNode(namedtuple("PrefixNode", ["op", "arg"])):
    def __str__(self):
        return "{}{}".format(self.op, wrap(self.arg))


class InfixNode(namedtuple("InfixNode", ["op", "left", "right"])):
    def __str__(self):
        return "{} {} {}".format(wrap(self.left), self.op, wrap(self.right))


def wrap(node):
    """Stringify the node and wrap it in parentheses if necessary."""
    if isinstance(node, InfixNode):
        return "(" + str(node) + ")"
    else:
        return str(node)


# Operator precedence
PREC_MAP = {TOKEN.PLUS: 1, TOKEN.MINUS: 1, TOKEN.SLASH: 2, TOKEN.ASTERISK: 2}
PREC_LOWEST = 0
PREC_PREFIX = 3
