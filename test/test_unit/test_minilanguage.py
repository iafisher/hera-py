from hera.debugger.minilanguage import (
    IntNode,
    MemoryNode,
    MiniLexer,
    MiniParser,
    MinusNode,
    RegisterNode,
    SymbolNode,
    TOKEN_AT,
    TOKEN_EOF,
    TOKEN_INT,
    TOKEN_MINUS,
    TOKEN_REGISTER,
    TOKEN_SYMBOL,
    TOKEN_UNKNOWN,
)


def test_lex_mini_language_with_small_example():
    lexer = MiniLexer("r1")

    assert lexer.next_token() == (TOKEN_REGISTER, "r1")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_lex_mini_language_with_big_example():
    # This isn't a syntactically valid expression, but it doesn't matter to the lexer.
    lexer = MiniLexer("@FP_alt R15 0xabc some_symbol -10 ?")

    assert lexer.next_token() == (TOKEN_AT, "@")
    assert lexer.next_token() == (TOKEN_REGISTER, "FP_alt")
    assert lexer.next_token() == (TOKEN_REGISTER, "R15")
    assert lexer.next_token() == (TOKEN_INT, "0xabc")
    assert lexer.next_token() == (TOKEN_SYMBOL, "some_symbol")
    assert lexer.next_token() == (TOKEN_MINUS, "-")
    assert lexer.next_token() == (TOKEN_INT, "10")
    assert lexer.next_token() == (TOKEN_UNKNOWN, "?")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_lex_mini_language_with_symbols_starting_with_M():
    lexer = MiniLexer("more m")

    assert lexer.next_token() == (TOKEN_SYMBOL, "more")
    assert lexer.next_token() == (TOKEN_SYMBOL, "m")
    assert lexer.next_token() == (TOKEN_EOF, "")
    assert lexer.next_token() == (TOKEN_EOF, "")


def test_parse_memory_expression():
    parser = MiniParser(MiniLexer("@@rt"))

    tree = parser.parse()

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, MemoryNode)
    assert isinstance(tree.address.address, RegisterNode)
    assert tree.address.address.value == "rt"


def test_parse_memory_expression_with_integer():
    parser = MiniParser(MiniLexer("@-0o12"))

    tree = parser.parse()

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, MinusNode)
    assert isinstance(tree.address.arg, IntNode)
    assert tree.address.arg.value == 0o12


def test_parse_memory_expression_with_symbol():
    parser = MiniParser(MiniLexer("@add"))

    tree = parser.parse()

    assert isinstance(tree, MemoryNode)
    assert isinstance(tree.address, SymbolNode)
    assert tree.address.value == "add"
