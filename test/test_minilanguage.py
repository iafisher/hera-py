from hera.debugger.minilanguage import (
    AssignNode,
    IntNode,
    MemoryNode,
    MiniLexer,
    MiniParser,
    RegisterNode,
    SymbolNode,
    TOKEN_ASSIGN,
    TOKEN_EOF,
    TOKEN_INT,
    TOKEN_LBRACKET,
    TOKEN_MEM,
    TOKEN_RBRACKET,
    TOKEN_REGISTER,
    TOKEN_SYMBOL,
)


def test_lex_mini_language_with_small_example():
    lexer = MiniLexer("r1")

    assert lexer.next_token() == (TOKEN_REGISTER, "r1")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_lex_mini_language_with_big_example():
    # This isn't a syntactically valid expression, but it doesn't matter to the lexer.
    lexer = MiniLexer("M[FP_alt] = R15 0xabc some_symbol")

    assert lexer.next_token() == (TOKEN_MEM, "M")
    assert lexer.next_token() == (TOKEN_LBRACKET, "[")
    assert lexer.next_token() == (TOKEN_REGISTER, "FP_alt")
    assert lexer.next_token() == (TOKEN_RBRACKET, "]")
    assert lexer.next_token() == (TOKEN_ASSIGN, "=")
    assert lexer.next_token() == (TOKEN_REGISTER, "R15")
    assert lexer.next_token() == (TOKEN_INT, "0xabc")
    assert lexer.next_token() == (TOKEN_SYMBOL, "some_symbol")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_parse_mini_language():
    parser = MiniParser(MiniLexer("M[M[rt]] = 0xfab"))

    tree = parser.parse()

    assert isinstance(tree, AssignNode)

    assert isinstance(tree.lhs, MemoryNode)
    assert isinstance(tree.lhs.address, MemoryNode)
    assert isinstance(tree.lhs.address.address, RegisterNode)
    assert tree.lhs.address.address.value == "rt"

    assert isinstance(tree.rhs, IntNode)
    assert tree.rhs.value == 0xFAB


def test_parse_mini_language_more():
    parser = MiniParser(MiniLexer("M[0o12] = add"))

    tree = parser.parse()

    assert isinstance(tree, AssignNode)

    assert isinstance(tree.lhs, MemoryNode)
    assert isinstance(tree.lhs.address, IntNode)
    assert tree.lhs.address.value == 0o12

    assert isinstance(tree.rhs, SymbolNode)
    assert tree.rhs.value == "add"
