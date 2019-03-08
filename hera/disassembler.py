from typing import List, Union

from . import op
from .data import HERAError, Token


# def disassemble(data: bytes) -> op.AbstractOperation:
def disassemble(data: bytes):
    if len(data) != 2:
        raise HERAError("all HERA operations are two bytes")

    hi, lo = data
    hi4 = hi >> 4
    midhi4 = hi & 0xF
    midlo4 = lo >> 4
    lo4 = lo & 0xF

    if hi4 == 0b1110:
        return op.SETLO(R(midhi4), UINT(lo))
    elif hi4 == 0b1111:
        return op.SETHI(R(midhi4), UINT(lo))
    elif hi4 == 0b1000:
        return op.AND(R(midhi4), R(midlo4), R(lo4))
    elif hi4 == 0b1001:
        return op.OR(R(midhi4), R(midlo4), R(lo4))
    elif hi4 == 0b1010:
        return op.ADD(R(midhi4), R(midlo4), R(lo4))
    elif hi4 == 0b1011:
        return op.SUB(R(midhi4), R(midlo4), R(lo4))
    elif hi4 == 0b1100:
        return op.MUL(R(midhi4), R(midlo4), R(lo4))
    elif hi4 == 0b1101:
        return op.XOR(R(midhi4), R(midlo4), R(lo4))
    elif hi4 == 0b0011:
        if midlo4 & 0b1000:
            r = R(midhi4)
            v = UINT(1 + lo4 + ((midlo4 & 0b0011) << 4))
            if midlo4 & 0b0100:
                return op.DEC(R(midhi4), v)
            else:
                return op.INC(R(midhi4), v)
        else:
            r1 = R(midhi4)
            r2 = R(lo4)
            if midlo4 == 0b000:
                return op.LSL(r1, r2)
            elif midlo4 == 0b001:
                return op.LSR(r1, r2)
            elif midlo4 == 0b010:
                return op.LSL8(r1, r2)
            elif midlo4 == 0b011:
                return op.LSR8(r1, r2)
            elif midlo4 == 0b100:
                return op.ASL(r1, r2)
            elif midlo4 == 0b101:
                return op.ASR(r1, r2)
            elif midlo4 == 0b110:
                flagop = midhi4 >> 1
                v = UINT(lo4 + ((midhi4 & 1) >> 4))
                if flagop == 0b000:
                    return op.FON(v)
                elif flagop == 0b100:
                    return op.FOFF(v)
                elif flagop == 0b010:
                    return op.FSET5(v)
                elif flagop == 0b110:
                    return op.FSET4(v)
            elif midlo4 == 0b111:
                if lo4 == 0b0000:
                    return op.SAVEF(r1)
                elif lo4 == 0b1000:
                    return op.RSTRF(r1)
    elif hi4 >> 2 == 0b01:
        offset = UINT(midlo4 + ((hi4 & 1) << 4))
        r1 = R(midhi4)
        r2 = R(lo4)
        if hi4 & 0b0010:
            return op.STORE(r1, offset, r2)
        else:
            return op.LOAD(r1, offset, r2)
    elif hi4 == 0b0001:
        r = R(lo4)
        if midhi4 == 0b0000:
            return op.BR(r)
        elif midhi4 == 0b0010:
            return op.BL(r)
        elif midhi4 == 0b0011:
            return op.BGE(r)
        elif midhi4 == 0b0100:
            return op.BLE(r)
        elif midhi4 == 0b0101:
            return op.BG(r)
        elif midhi4 == 0b0110:
            return op.BULE(r)
        elif midhi4 == 0b0111:
            return op.BUG(r)
        elif midhi4 == 0b1000:
            return op.BZ(r)
        elif midhi4 == 0b1001:
            return op.BNZ(r)
        elif midhi4 == 0b1010:
            return op.BC(r)
        elif midhi4 == 0b1011:
            return op.BNC(r)
        elif midhi4 == 0b1100:
            return op.BS(r)
        elif midhi4 == 0b1101:
            return op.BNS(r)
        elif midhi4 == 0b1110:
            return op.BV(r)
        elif midhi4 == 0b1111:
            return op.BNV(r)
    elif hi4 == 0b0000:
        if midhi4 == 0b0000:
            return op.BRR(r)
        elif midhi4 == 0b0010:
            return op.BLR(r)
        elif midhi4 == 0b0011:
            return op.BGER(r)
        elif midhi4 == 0b0100:
            return op.BLER(r)
        elif midhi4 == 0b0101:
            return op.BGR(r)
        elif midhi4 == 0b0110:
            return op.BULER(r)
        elif midhi4 == 0b0111:
            return op.BUGR(r)
        elif midhi4 == 0b1000:
            return op.BZR(r)
        elif midhi4 == 0b1001:
            return op.BNZR(r)
        elif midhi4 == 0b1010:
            return op.BCR(r)
        elif midhi4 == 0b1011:
            return op.BNCR(r)
        elif midhi4 == 0b1100:
            return op.BSR(r)
        elif midhi4 == 0b1101:
            return op.BNSR(r)
        elif midhi4 == 0b1110:
            return op.BVR(r)
        elif midhi4 == 0b1111:
            return op.BNVR(r)
    elif hi4 == 0b0010 and midhi4 >> 1 == 0b000:
        if midhi4 & 1:
            return op.RETURN(R(midlo4), R(lo4))
        else:
            return op.CALL(R(midlo4), R(lo4))
    elif hi == 0b00100010 and midlo4 == 0b0000:
        return op.SWI(UINT(lo4))
    elif hi == 0b00100011 and lo == 0:
        return op.RTI()

    raise HERAError("unknown instruction")


def match(pattern: str, v: int) -> Union[List, bool]:
    """Try to match the 16-bit integer `v` against `pattern`. Return a list of
    extracted arguments if `v` matches, or False otherwise.

    `pattern` should be a string of sixteen characters, which may be the digits '0' or
    '1' or lowercase Latin letters. The digits are matched against the literal digits
    in `v`; letters are used to extract values. For example, "0000aaaabbbb1111" would
    match, e.g., 0000 1001 0110 11111, returning [0b1001, 0b0110].
    """
    s = bin(v)[2:].rjust(16, "0")
    args = []  # type: List[int]

    for pattern_bit, real_bit in zip(pattern, s):
        if pattern_bit == "0":
            if real_bit != "0":
                return False
        elif pattern_bit == "1":
            if real_bit != "1":
                return False
        else:
            index = ord(pattern_bit) - ord("a")
            while index >= len(args):
                args.append(0)

            args[index] <<= 1
            if real_bit == "1":
                args[index] += 1

    return args


def R(v):
    return Token(Token.REGISTER, v)


def UINT(v):
    return Token(Token.INT, v)
