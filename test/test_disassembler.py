from hera.main import main


def test_disassemble_set_inc(capsys):
    main(["disassemble", "test/assets/asm/set_inc.hera.lcode"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert (
        captured.out
        == """\
SETLO(R1, 255)
SETHI(R3, 42)
INC(R10, 1)
DEC(R1, 20)
"""
    )


def test_disassemble_binary_op(capsys):
    main(["disassemble", "test/assets/asm/binary_op.hera.lcode"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert (
        captured.out
        == """\
AND(R1, R7, R12)
OR(R0, R4, R2)
ADD(R3, R5, R8)
SUB(R9, R13, R15)
MUL(R1, R2, R3)
XOR(R8, R7, R4)
"""
    )


def test_disassemble_branch(capsys):
    main(["disassemble", "test/assets/asm/branch.hera.lcode"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert (
        captured.out
        == """\
BR(R1)
BL(R1)
BGE(R1)
BLE(R1)
BG(R1)
BULE(R1)
BUG(R1)
BZ(R1)
BNZ(R1)
BC(R1)
BNC(R1)
BS(R1)
BNS(R1)
BV(R1)
BNV(R1)
CALL(R12, R11)
RETURN(R12, R13)
"""
    )


def test_disassemble_flag(capsys):
    main(["disassemble", "test/assets/asm/flag.hera.lcode"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert (
        captured.out
        == """\
SAVEF(R5)
RSTRF(R5)
FON(4)
FOFF(5)
FSET5(3)
FSET4(2)
"""
    )


def test_disassemble_shift(capsys):
    main(["disassemble", "test/assets/asm/shift.hera.lcode"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert (
        captured.out
        == """\
LSL(R3, R4)
LSR(R5, R6)
LSL8(R7, R8)
LSR8(R8, R9)
ASL(R1, R2)
ASR(R2, R3)
"""
    )


def test_disassemble_misc(capsys):
    main(["disassemble", "test/assets/asm/misc.hera.lcode"])

    captured = capsys.readouterr()
    assert captured.err == ""
    assert (
        captured.out
        == """\
LOAD(R1, 10, R14)
STORE(R2, 0, R14)
SWI(10)
RTI()
"""
    )
