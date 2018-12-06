import logging
from diana.guid.mint import GUIDMint

def test_guids():

    M = GUIDMint()

    expected = ('VV4SBNF2YLQW52WCIVZHSNGXIULV4MJV', 'VANHARLINGEN^VANCE^4', '20080209')

    s = "FOO^BAR^Z^^"
    age = 10
    reference_date = "2018-01-01"

    out = M.get_sham_id(name=s, age=age, reference_date=reference_date)
    logging.debug(out)

    assert( out == expected )

    s = "Foo, Bar Z"
    age = 10
    reference_date = "Jan 1, 2018"

    out = M.get_sham_id(name=s, age=age, reference_date=reference_date)
    logging.debug(out)

    assert( out == expected )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_guids()



