import logging
from diana.utils.guid.mint import GUIDMint

def test_guids():

    M = GUIDMint()

    expected = ('JGHVCZSDBOFIA2QZ4H6EI43K4HAPB3IM', 'JAMESON^GRAHAM^H', '20080209')

    s = "FOO^BAR^Z^^"
    age = 10
    reference_date = "2018-01-01"

    out = M.get_sham_id(name=s, age=age, reference_date=reference_date)
    logging.debug(out)

    assert( out == expected )

    s = "Foo, Bar Z"
    age = 10
    reference_date = "1/1/2018"

    out = M.get_sham_id(name=s, age=age, reference_date=reference_date)
    logging.debug(out)

    s = "Bar Z Foo"
    age = 10
    reference_date = "January 1, 2018"

    out = M.get_sham_id(name=s, age=age, reference_date=reference_date)
    logging.debug(out)


    assert( out == expected )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_guids()



