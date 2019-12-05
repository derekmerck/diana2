"""
Short-hand string signature algorithm for self-verifying transcriptions
"""


from typing import Callable
from base64 import _b32alphabet

def str_crc(str_in: str, encoder: Callable=None):

    if not isinstance(str_in, str):
        raise TypeError

    sum = 0
    for ch in str_in:
        sum += ord( ch )

    if encoder:
        crc = encoder( sum )
    else:
        crc = sum

    return crc


def mk_crc(str_in: str, encoder: Callable=None):
    crc = str_crc(str_in, encoder=encoder)
    return f"{str_in}+{crc}"


def chk_crc(str_in: str, encoder: Callable=None):

    _str_in, _crc = str_in.split('+')
    crc = str_crc(_str_in, encoder=encoder)

    if not encoder:
        # The crc is just an int as a string
        _crc = int(_crc)

    if crc == _crc:
        return True

    return False


def b32char(val: int):

    val = val % 32
    item = _b32alphabet[val]
    char = chr( item )
    return char

