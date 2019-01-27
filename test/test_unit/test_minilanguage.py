from hera.debugger.minilanguage import (
    BoolNode,
    IntNode,
    MemoryNode,
    MiniLexer,
    MiniParser,
    RegisterNode,
    SymbolNode,
    TOKEN_EOF,
    TOKEN_FALSE,
    TOKEN_INT,
    TOKEN_MEM,
    TOKEN_RBRACKET,
    TOKEN_REGISTER,
    TOKEN_SYMBOL,
    TOKEN_TRUE,
)


def test_lex_mini_language_with_small_example():
    lexer = MiniLexer("r1")

    assert lexer.next_token() == (TOKEN_REGISTER, "r1")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_lex_mini_language_with_big_example():
    # This isn't a syntactically valid expression, but it doesn't matter to the lexer.
    lexer = MiniLexer("M[FP_alt] R15 0xabc some_symbol #t #F")

    assert lexer.next_token() == (TOKEN_MEM, "M[")
    assert lexer.next_token() == (TOKEN_REGISTER, "FP_alt")
    assert lexer.next_token() == (TOKEN_RBRACKET, "]")
    assert lexer.next_token() == (TOKEN_REGISTER, "R15")
    assert lexer.next_token() == (TOKEN_INT, "0xabc")
    assert lexer.next_token() == (TOKEN_SYMBOL, "some_symbol")
    assert lexer.next_token() == (TOKEN_TRUE, "#t")
    assert lexer.next_token() == (TOKEN_FALSE, "#F")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_lex_mini_language_with_symbols_starting_with_M():
    lexer = MiniLexer("more m")

    assert lexer.next_token() == (TOKEN_SYMBOL, "more")
    assert lexer.next_token() == (TOKEN_SYMBOL, "m")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_parse_memory_expression():
    parser = MiniParser(MiniLexer("M[M[rt]]"))

    tree = parser.parse()

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, MemoryNode)
    assert isinstance(tree.address.address, RegisterNode)
    assert tree.address.address.value == "rt"


def test_parse_memory_expression_with_integer():
    parser = MiniParser(MiniLexer("M[0o12]"))

    tree = parser.parse()

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, IntNode)
    assert tree.address.value == 0o12


def test_parse_boolean():
    parser = MiniParser(MiniLexer("#t"))

    tree = parser.parse()

    assert isinstance(tree, BoolNode)
    assert tree.value is True


def test_parse_memory_expression_with_symbol():
    parser = MiniParser(MiniLexer("M[add]"))

    tree = parser.parse()

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, SymbolNode)
    assert tree.address.value == "add"
