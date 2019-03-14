"""
The parser for the debugger's expression mini-language.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: January 2019
"""
from collections import namedtuple

from ..lexer import Lexer
from ..data import HERAError, Token
from ..utils import register_to_index


def parse(line: str) -> "SeqNode":
    """
    Return a parse tree for the line of code. Raise a SyntaxError if it is not well-
    formatted.
    """
    return MiniParser(Lexer(line)).parse()


class MiniParser:
    """
    A parser for the debugger's expression mini-language. The abstract grammar below
    describes the language. Arithmetic operations have the usual precedence.

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

    def __init__(self, lexer: Lexer) -> None:
        self.lexer = lexer

    def parse(self) -> "SeqNode":
        tree = self.match_exprlist()
        if self.lexer.tkn.type == Token.EOF:
            return tree
        else:
            raise SyntaxError("trailing input")

    def match_exprlist(self) -> "SeqNode":
        """Match a sequence of comma-separated expressions."""
        seq = []

        if self.lexer.tkn.type == Token.FMT:
            fmt = self.lexer.tkn.value
            self.lexer.next_token()
        else:
            fmt = ""

        while True:
            expr = self.match_expr(PREC_LOWEST)
            seq.append(expr)
            if self.lexer.tkn.type == Token.COMMA:
                self.lexer.next_token()
            else:
                break

        return SeqNode(fmt, seq)

    def match_expr(self, precedence: int) -> "AbstractNode":
        """Parse the expression with the given precedence."""
        tkn = self.lexer.tkn
        # This line is solely to satisfy mypy.
        left = AbstractNode()
        if tkn.type == Token.AT:
            self.lexer.next_token()
            address = self.match_expr(PREC_PREFIX)
            left = MemoryNode(address)
        elif tkn.type == Token.INT:
            try:
                left = IntNode(int(tkn.value, base=0))
            except ValueError:
                raise SyntaxError("invalid integer literal: {}".format(tkn))
            else:
                self.lexer.next_token()
        elif tkn.type == Token.MINUS:
            self.lexer.next_token()
            left = PrefixNode("-", self.match_expr(PREC_PREFIX))
        elif tkn.type == Token.REGISTER:
            try:
                left = RegisterNode(register_to_index(tkn.value))
            except HERAError:
                raise SyntaxError("{} is not a valid register".format(tkn.value))
            self.lexer.next_token()
        elif tkn.type == Token.SYMBOL:
            left = SymbolNode(tkn.value)
            self.lexer.next_token()
        elif tkn.type == Token.LPAREN:
            self.lexer.next_token()
            left = self.match_expr(PREC_LOWEST)
            if self.lexer.tkn.type != Token.RPAREN:
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

    def unexpected(self, tkn: Token) -> None:
        if tkn.type == Token.EOF:
            raise SyntaxError("premature end of input")
        elif tkn.type == Token.UNKNOWN:
            raise SyntaxError("unrecognized input `{}`".format(tkn))
        else:
            raise SyntaxError("did not expect `{}` in this position".format(tkn))


class AbstractNode:
    """An abstract base class for AST nodes. Used for type annotations."""


class SeqNode(namedtuple("SeqNode", ["fmt", "seq"]), AbstractNode):
    def __str__(self):
        seqstr = ", ".join(map(str, self.seq))
        if self.fmt:
            return ":{} {}".format(self.fmt, seqstr)
        else:
            return seqstr


class MemoryNode(namedtuple("MemoryNode", ["address"]), AbstractNode):
    def __str__(self):
        return "@{}".format(wrap(self.address))


class RegisterNode(namedtuple("RegisterNode", ["value"]), AbstractNode):
    def __str__(self):
        return "R" + str(self.value)


class IntNode(namedtuple("IntNode", ["value"]), AbstractNode):
    def __str__(self):
        return str(self.value)


class SymbolNode(namedtuple("SymbolNode", ["value"]), AbstractNode):
    def __str__(self):
        return self.value


class PrefixNode(namedtuple("PrefixNode", ["op", "arg"]), AbstractNode):
    def __str__(self):
        return "{}{}".format(self.op, wrap(self.arg))


class InfixNode(namedtuple("InfixNode", ["op", "left", "right"]), AbstractNode):
    def __str__(self):
        return "{} {} {}".format(wrap(self.left), self.op, wrap(self.right))


def wrap(node: AbstractNode) -> str:
    """Stringify the node and wrap it in parentheses if necessary."""
    if isinstance(node, InfixNode):
        return "(" + str(node) + ")"
    else:
        return str(node)


# Operator precedence
PREC_MAP = {Token.PLUS: 1, Token.MINUS: 1, Token.SLASH: 2, Token.ASTERISK: 2}
PREC_LOWEST = 0
PREC_PREFIX = 3
