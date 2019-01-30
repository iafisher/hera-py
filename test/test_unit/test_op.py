from hera.data import Constant, DataLabel, IntToken, Label, Token, TOKEN
from hera.op import (
    check_in_range,
    check_label,
    check_register,
    check_register_or_label,
    check_string,
    SET,
)


def R(s):
    return Token(TOKEN.REGISTER, s)


def SYM(s):
    return Token(TOKEN.SYMBOL, s)


def STR(s):
    return Token(TOKEN.STRING, s)


def test_op_to_string():
    assert str(SET(R("R1"), SYM("top"))) == "SET(R1, top)"


def test_op_to_string_with_integer():
    assert str(SET(R("R1"), IntToken(12))) == "SET(R1, 12)"


def test_check_register_with_non_register():
    assert check_register(IntToken(10)) == "expected register"


def test_check_register_with_program_counter():
    assert (
        check_register(R("PC"))
        == "program counter cannot be accessed or changed directly"
    )


def test_check_register_with_invalid_register():
    assert check_register(R("R17")) == "R17 is not a valid register"


def test_check_register_with_valid_registers():
    assert check_register(R("R0")) is None
    assert check_register(R("R1")) is None
    assert check_register(R("Rt")) is None
    assert check_register(R("FP")) is None
    assert check_register(R("SP")) is None
    assert check_register(R("FP_alt")) is None
    assert check_register(R("PC_ret")) is None


def test_check_register_or_label_with_integer():
    assert check_register_or_label(IntToken(10), {}) == "expected register or label"


def test_check_register_or_label_with_undefined_symbol():
    assert check_register_or_label(SYM("n"), {}) == "undefined symbol"


def test_check_register_or_label_with_constant():
    err = check_register_or_label(SYM("n"), {"n": Constant(1)})
    assert err == "constant cannot be used as label"


def test_check_register_or_label_with_data_label():
    err = check_register_or_label(SYM("n"), {"n": DataLabel(1)})
    assert err == "data label cannot be used as branch label"


def test_check_register_or_label_with_valid_args():
    assert check_register_or_label(R("R7"), {}) is None
    assert check_register_or_label(SYM("n"), {"n": Label(1)}) is None


def test_check_label_with_non_label():
    assert check_label(R("R1")) == "expected label"


def test_check_label_with_valid_label():
    assert check_label(SYM("l")) is None


def test_check_string_with_non_string():
    assert check_string(R("R7")) == "expected string literal"
    assert check_string(SYM("hello")) == "expected string literal"


def test_check_string_with_valid_string():
    assert check_string(STR("hello")) is None


def test_check_in_range_with_undefined_symbol():
    assert check_in_range(SYM("n"), {}, lo=0, hi=128) == "undefined constant"


def test_check_in_range_with_label():
    err = check_in_range(SYM("n"), {"n": Label(1)}, lo=0, hi=128)
    assert err == "cannot use label as constant"


def test_check_in_range_with_data_label():
    err = check_in_range(SYM("n"), {"n": DataLabel(1)}, lo=0, hi=128)
    assert err == "cannot use label as constant"


def test_check_in_range_with_non_integer():
    assert check_in_range(R("R1"), {}, lo=0, hi=128) == "expected integer"


def test_check_in_range_with_out_of_range_integer():
    err = check_in_range(IntToken(-1), {}, lo=0, hi=128)
    assert err == "integer must be in range [0, 128)"


def test_check_in_range_with_another_out_of_range_integer():
    err = check_in_range(IntToken(128), {}, lo=0, hi=128)
    assert err == "integer must be in range [0, 128)"


def test_check_in_range_with_out_of_range_symbol():
    err = check_in_range(SYM("n"), {"n": Constant(128)}, lo=0, hi=128)
    assert err == "integer must be in range [0, 128)"


def test_check_in_range_with_valid_integers():
    assert check_in_range(IntToken(50), {}, lo=0, hi=128) is None
    assert check_in_range(IntToken(0), {}, lo=0, hi=128) is None
    assert check_in_range(IntToken(127), {}, lo=0, hi=128) is None
    assert check_in_range(SYM("n"), {"n": Constant(127)}, lo=0, hi=128) is None
