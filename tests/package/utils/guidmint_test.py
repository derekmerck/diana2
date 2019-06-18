import logging, datetime
from pprint import pprint
from diana.utils.guid import GUIDMint

def test_guid_genders():

    M = GUIDMint()

    expected = {
        'ID': 'WHLOKMAGICLQGYKC3ZQLLMFKMOX3ZAP2',
        'Name': ['WAGENAAR', 'HERIBERTO', 'L'],
        'BirthDate': datetime.date(1999, 10, 8),
        'TimeOffset': datetime.timedelta(-86, 85464)
    }

    s = "Bar Z Foo"
    dob = "2000-01-01"

    out = M.get_sham_id(name=s, dob=dob)
    assert( out == expected )

    out = M.get_sham_id(name=s, dob=dob, gender="U")
    assert( out == expected )

    out = M.get_sham_id(name=s, dob=dob, gender="u")
    assert( out == expected )

    out = M.get_sham_id(name=s, dob=dob, gender="UNKNOWN")
    assert( out == expected )

    out = M.get_sham_id(name=s, dob=dob, gender="unknown")
    assert( out == expected )

    out = M.get_sham_id(name=s, dob=dob, gender="")
    assert( out == expected )

    out = M.get_sham_id(name=s, dob=dob, gender="ABCD")
    assert( out == expected )

    expected = {'BirthDate': datetime.date(2000, 2, 19),
                'ID': 'HNG54O6PWWEIVTTQCYCVIYBENW4RK64G',
                'Name': ['HOWDESHELL', 'NELSON', 'G'],
                'TimeOffset': datetime.timedelta(48, 84883)}

    out = M.get_sham_id(name=s, dob=dob, gender="M")
    assert( out == expected )

    out = M.get_sham_id(name=s, dob=dob, gender="male")
    assert( out == expected )

    expected = {'BirthDate': datetime.date(1999, 10, 19),
                'ID': 'SIDYPTGPM27TDCMQOPSXFOAXECXJGOZZ',
                'Name': ['SARSON', 'IRENA', 'D'],
                'TimeOffset': datetime.timedelta(-74, 1033)}

    out = M.get_sham_id(name=s, dob=dob, gender="F")
    assert( out == expected )

    out = M.get_sham_id(name=s, dob=dob, gender="female")
    assert( out == expected )

def test_guids():

    M = GUIDMint()

    expected = {
        'ID': 'JGHVCZSDBOFIA2QZ4H6EI43K4HAPB3IM',
        'Name': ['JACKSITS', 'GENE', 'H'],
        'BirthDate': datetime.date(2007, 10, 8),
        'TimeOffset': datetime.timedelta(-86, 3040)
    }

    # expected = ('JGHVCZSDBOFIA2QZ4H6EI43K4HAPB3IM', 'JAMESON^GRAHAM^H', '20080209')

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
    test_guid_genders()
