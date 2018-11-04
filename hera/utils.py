"""Utilities for the HERA interpreter.

Author:  Ian Fisher (iafisher@protonmail.com)
Version: November 2018
"""


def to_uint(n):
    """Convert the number to its unsigned representation as a 16-bit integer.
    If `n` is non-negative, then it is returned unchanged. If `n` is negative,
    an unsigned integer is returned whose binary representation is identical to
    the two's complement representation of `n` as a 16-bit signed integer.

    If `n` is negative and too large to represent as a 16-bit integer, then a
    ValueError is raised.
    """
    if n < 0:
        if n < -2**15:
            raise ValueError('signed integer too large for 16 bits')
        return 2**16+n
    else:
        return n


def from_uint(n):
    """Reinterpret the number from an unsigned 16-bit integer to a signed 16-bit
    integer.
    """
    if n >= 2**15:
        return -(2**16-n)
    else:
        return n
