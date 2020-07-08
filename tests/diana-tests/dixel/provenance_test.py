import logging
from diana.dixel import Provenance
from datetime import datetime


def test_provenance():

    fkey = b'4XUWuDib1xuCK8Czchg0pNquGO69BGuoIoA5lfW2tpA='

    p = Provenance(
        institution="test_inst",
        trial="test_proj",
        original_study_dt=datetime(year=1900, month=1, day=1,
                                   hour=0, minute=0, second=0)
    )
    logging.debug(p)

    tok = p.to_token(fkey)
    logging.debug(tok)

    p2 = Provenance.from_token(tok, fkey)
    logging.debug(p2)

    assert(p == p2)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_provenance()
