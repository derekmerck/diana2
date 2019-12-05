
from diana.utils import str_crc, mk_crc, chk_crc, b32char

def test_str_crc():

    crc = str_crc("Hello123")

    print(crc)
    assert( crc == 650 )

    signed = mk_crc("Hello123")

    print(signed)
    assert( signed=="Hello123+650" )

    assert( chk_crc(signed) )

    crc = str_crc("Hello123", encoder=b32char)
    print(crc)
    assert( crc == "K" )

    signed = mk_crc("Hello123", encoder=b32char)

    print(signed)
    assert(signed=="Hello123+K")

    assert( chk_crc(signed, encoder=b32char) )


if __name__ == "__main__":

    test_str_crc()