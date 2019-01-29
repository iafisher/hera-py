from hera.debugger.minilanguage import (
    AddNode,
    DivNode,
    IntNode,
    MemoryNode,
    MiniLexer,
    MiniParser,
    MinusNode,
    MulNode,
    RegisterNode,
    SeqNode,
    SubNode,
    SymbolNode,
    TOKEN_ASTERISK,
    TOKEN_AT,
    TOKEN_COMMA,
    TOKEN_EOF,
    TOKEN_FMT,
    TOKEN_INT,
    TOKEN_LPAREN,
    TOKEN_MINUS,
    TOKEN_PLUS,
    TOKEN_REGISTER,
    TOKEN_RPAREN,
    TOKEN_SLASH,
    TOKEN_SYMBOL,
    TOKEN_UNKNOWN,
)


def lex_helper(text):
    return MiniLexer(text)


def parse_helper(text, keep_seq=False):
    tree = MiniParser(MiniLexer(text)).parse()
    if not keep_seq and isinstance(tree, SeqNode):
        assert len(tree.seq) == 1
        return tree.seq[0]
    else:
        return tree


def test_lex_mini_language_with_small_example():
    lexer = lex_helper("r1")

    assert lexer.next_token() == (TOKEN_REGISTER, "r1")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_lex_mini_language_with_big_example():
    # This isn't a syntactically valid expression, but it doesn't matter to the lexer.
    lexer = lex_helper("@FP_alt R15 0xabc some_symbol :xdc -10 ,, ()+*/?")

    assert lexer.next_token() == (TOKEN_AT, "@")
    assert lexer.next_token() == (TOKEN_REGISTER, "FP_alt")
    assert lexer.next_token() == (TOKEN_REGISTER, "R15")
    assert lexer.next_token() == (TOKEN_INT, "0xabc")
    assert lexer.next_token() == (TOKEN_SYMBOL, "some_symbol")
    assert lexer.next_token() == (TOKEN_FMT, "xdc")
    assert lexer.next_token() == (TOKEN_MINUS, "-")
    assert lexer.next_token() == (TOKEN_INT, "10")
    assert lexer.next_token() == (TOKEN_COMMA, ",")
    assert lexer.next_token() == (TOKEN_COMMA, ",")
    assert lexer.next_token() == (TOKEN_LPAREN, "(")
    assert lexer.next_token() == (TOKEN_RPAREN, ")")
    assert lexer.next_token() == (TOKEN_PLUS, "+")
    assert lexer.next_token() == (TOKEN_ASTERISK, "*")
    assert lexer.next_token() == (TOKEN_SLASH, "/")
    assert lexer.next_token() == (TOKEN_UNKNOWN, "?")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_lex_mini_language_with_symbols_starting_with_M():
    lexer = lex_helper("more m")

    assert lexer.next_token() == (TOKEN_SYMBOL, "more")
    assert lexer.next_token() == (TOKEN_SYMBOL, "m")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_parse_memory_expression():
    tree = parse_helper("@@rt")

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, MemoryNode)
    assert isinstance(tree.address.address, RegisterNode)
    assert tree.address.address.value == "rt"


def test_parse_memory_expression_with_integer():
    tree = parse_helper("@-0o12")

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, MinusNode)
    assert isinstance(tree.address.arg, IntNode)
    assert tree.address.arg.value == 0o12


def test_parse_memory_expression_with_symbol():
    tree = parse_helper("@add")

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, SymbolNode)
    assert tree.address.value == "add"


def test_parse_simple_arithmetic():
    tree = parse_helper("1 + 2 * 3")

    assert isinstance(tree, AddNode)

    assert isinstance(tree.left, IntNode)
    assert tree.left.value == 1

    assert isinstance(tree.right, MulNode)
    assert isinstance(tree.right.left, IntNode)
    assert isinstance(tree.right.right, IntNode)
    assert tree.right.left.value == 2
    assert tree.right.right.value == 3


def test_parse_grouped_arithmetic():
    tree = parse_helper("(1 + 2) * (3 + 4)")

    assert isinstance(tree, MulNode)

    assert isinstance(tree.left, AddNode)
    assert isinstance(tree.left.left, IntNode)
    assert tree.left.left.value == 1
    assert isinstance(tree.left.right, IntNode)
    assert tree.left.right.value == 2

    assert isinstance(tree.right, AddNode)
    assert isinstance(tree.right.left, IntNode)
    assert tree.right.left.value == 3
    assert isinstance(tree.right.right, IntNode)
    assert tree.right.right.value == 4


def test_parse_complicated_arithmetic():
    tree = parse_helper("@((1+2) /-0o123) + @@5 - r1")

    assert isinstance(tree, AddNode)

    assert isinstance(tree.left, MemoryNode)
    assert isinstance(tree.left.address, DivNode)
    assert isinstance(tree.left.address.left, AddNode)
    assert isinstance(tree.left.address.left.left, IntNode)
    assert isinstance(tree.left.address.left.right, IntNode)
    assert tree.left.address.left.left.value == 1
    assert tree.left.address.left.right.value == 2

    assert isinstance(tree.right, SubNode)
    assert isinstance(tree.right.left, MemoryNode)
    assert isinstance(tree.right.left.address, MemoryNode)
    assert isinstance(tree.right.left.address.address, IntNode)
    assert tree.right.left.address.address.value == 5
    assert isinstance(tree.right.right, RegisterNode)
    assert tree.right.right.value == "r1"


def test_parse_expression_with_format_spec():
    tree = parse_helper(":y R1", keep_seq=True)

    assert isinstance(tree, SeqNode)
    assert tree.fmt == "y"
    assert len(tree.seq) == 1

    assert isinstance(tree.seq[0], RegisterNode)
    assert tree.seq[0].value == "R1"


def test_parse_sequence_of_expressions():
    tree = parse_helper("r1, @r2, 1 + 3", keep_seq=True)

    assert isinstance(tree, SeqNode)
    assert tree.fmt == ""
    assert len(tree.seq) == 3

    assert isinstance(tree.seq[0], RegisterNode)
    assert tree.seq[0].value == "r1"

    assert isinstance(tree.seq[1], MemoryNode)
    assert isinstance(tree.seq[1].address, RegisterNode)
    assert tree.seq[1].address.value == "r2"

    assert isinstance(tree.seq[2], AddNode)
    assert isinstance(tree.seq[2].left, IntNode)
    assert isinstance(tree.seq[2].right, IntNode)
    assert tree.seq[2].left.value == 1
    assert tree.seq[2].right.value == 3


def test_parse_sequence_of_expressions_with_format_spec():
    tree = parse_helper(":xdc r1, r2", keep_seq=True)

    assert isinstance(tree, SeqNode)
    assert tree.fmt == "xdc"
    assert len(tree.seq) == 2

    assert isinstance(tree.seq[0], RegisterNode)
    assert tree.seq[0].value == "r1"

    assert isinstance(tree.seq[1], RegisterNode)
    assert tree.seq[1].value == "r2"
