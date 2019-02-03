import pytest

from hera.debugger.miniparser import (
    InfixNode,
    IntNode,
    MemoryNode,
    Lexer,
    MiniParser,
    RegisterNode,
    SeqNode,
    SymbolNode,
)


def parse_helper(text, keep_seq=False):
    tree = MiniParser(Lexer(text)).parse()
    if not keep_seq and isinstance(tree, SeqNode):
        assert len(tree.seq) == 1
        return tree.seq[0]
    else:
        return tree


def test_parse_memory_expression():
    tree = parse_helper("@@rt")
    assert str(tree) == "@@R11"

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, MemoryNode)
    assert isinstance(tree.address.address, RegisterNode)
    assert tree.address.address.value == 11


def test_parse_memory_expression_with_integer():
    tree = parse_helper("@-0o12")
    assert str(tree) == "@-10"

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, IntNode)
    assert tree.address.value == -0o12


def test_parse_memory_expression_with_symbol():
    tree = parse_helper("@add")
    assert str(tree) == "@add"

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, SymbolNode)
    assert tree.address.value == "add"


def test_parse_simple_arithmetic():
    tree = parse_helper("1 + 2 * 3")
    assert str(tree) == "1 + (2 * 3)"

    assert isinstance(tree, InfixNode)
    assert tree.op == "+"

    assert isinstance(tree.left, IntNode)
    assert tree.left.value == 1

    assert isinstance(tree.right, InfixNode)
    assert tree.right.op == "*"
    assert isinstance(tree.right.left, IntNode)
    assert isinstance(tree.right.right, IntNode)
    assert tree.right.left.value == 2
    assert tree.right.right.value == 3


def test_parse_grouped_arithmetic():
    tree = parse_helper("(1 + 2) * (3 + 4)")
    assert str(tree) == "(1 + 2) * (3 + 4)"

    assert isinstance(tree, InfixNode)
    assert tree.op == "*"

    assert isinstance(tree.left, InfixNode)
    assert tree.left.op == "+"
    assert isinstance(tree.left.left, IntNode)
    assert tree.left.left.value == 1
    assert isinstance(tree.left.right, IntNode)
    assert tree.left.right.value == 2

    assert isinstance(tree.right, InfixNode)
    assert tree.right.op == "+"
    assert isinstance(tree.right.left, IntNode)
    assert tree.right.left.value == 3
    assert isinstance(tree.right.right, IntNode)
    assert tree.right.right.value == 4


def test_parse_complicated_arithmetic():
    tree = parse_helper("@((1+2) /-0o123) + @@5 - r1")
    assert str(tree) == "(@((1 + 2) / -83) + @@5) - R1"

    assert isinstance(tree, InfixNode)
    assert tree.op == "-"

    assert isinstance(tree.left, InfixNode)
    assert tree.left.op == "+"
    assert isinstance(tree.left.left, MemoryNode)
    assert isinstance(tree.left.left.address, InfixNode)
    assert tree.left.left.address.op == "/"
    assert isinstance(tree.left.left.address.left, InfixNode)
    assert tree.left.left.address.left.op == "+"
    assert isinstance(tree.left.left.address.left.left, IntNode)
    assert isinstance(tree.left.left.address.left.right, IntNode)
    assert tree.left.left.address.left.left.value == 1
    assert tree.left.left.address.left.right.value == 2
    assert isinstance(tree.left.right, MemoryNode)
    assert isinstance(tree.left.right.address, MemoryNode)
    assert isinstance(tree.left.right.address.address, IntNode)
    assert tree.left.right.address.address.value == 5

    assert isinstance(tree.right, RegisterNode)
    assert tree.right.value == 1


def test_parse_tricky_precedence():
    tree = parse_helper("1*2+3")
    assert str(tree) == "(1 * 2) + 3"

    assert isinstance(tree, InfixNode)
    assert tree.op == "+"

    assert isinstance(tree.left, InfixNode)
    assert tree.left.op == "*"
    assert isinstance(tree.left.left, IntNode)
    assert tree.left.left.value == 1
    assert isinstance(tree.left.right, IntNode)
    assert tree.left.right.value == 2

    assert isinstance(tree.right, IntNode)
    assert tree.right.value == 3


def test_parse_expression_with_format_spec():
    tree = parse_helper(":y R1", keep_seq=True)
    assert str(tree) == ":y R1"

    assert isinstance(tree, SeqNode)
    assert tree.fmt == "y"
    assert len(tree.seq) == 1

    assert isinstance(tree.seq[0], RegisterNode)
    assert tree.seq[0].value == 1


def test_parse_sequence_of_expressions():
    tree = parse_helper("r1, @r2, 1 + 3", keep_seq=True)
    assert str(tree) == "R1, @R2, 1 + 3"

    assert isinstance(tree, SeqNode)
    assert tree.fmt == ""
    assert len(tree.seq) == 3

    assert isinstance(tree.seq[0], RegisterNode)
    assert tree.seq[0].value == 1

    assert isinstance(tree.seq[1], MemoryNode)
    assert isinstance(tree.seq[1].address, RegisterNode)
    assert tree.seq[1].address.value == 2

    assert isinstance(tree.seq[2], InfixNode)
    assert tree.seq[2].op == "+"
    assert isinstance(tree.seq[2].left, IntNode)
    assert isinstance(tree.seq[2].right, IntNode)
    assert tree.seq[2].left.value == 1
    assert tree.seq[2].right.value == 3


def test_parse_sequence_of_expressions_with_format_spec():
    tree = parse_helper(":xdc fp, sp", keep_seq=True)
    assert str(tree) == ":xdc R14, R15"

    assert isinstance(tree, SeqNode)
    assert tree.fmt == "xdc"
    assert len(tree.seq) == 2

    assert isinstance(tree.seq[0], RegisterNode)
    assert tree.seq[0].value == 14

    assert isinstance(tree.seq[1], RegisterNode)
    assert tree.seq[1].value == 15


def test_parse_with_trailing_input():
    with pytest.raises(SyntaxError):
        parse_helper("1+2 3")


def test_parse_with_invalid_octal_literal():
    with pytest.raises(SyntaxError):
        parse_helper("0o9")


def test_parse_with_unclosed_parenthesis():
    with pytest.raises(SyntaxError):
        parse_helper("(1 + 2")


def test_parse_with_unrecognized_character():
    with pytest.raises(SyntaxError):
        parse_helper("?1")


def test_parse_with_unexpected_token():
    with pytest.raises(SyntaxError):
        parse_helper(")1+2)")
