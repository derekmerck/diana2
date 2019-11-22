import logging, os
from pathlib import Path
from datetime import date
from diana.dixel import Dixel, ShamDixel
from diana.apis import CsvFile


def test_csv(tmp_path):

    fp = tmp_path / "tmp.csv"

    ep0 = CsvFile(fp=fp)
    ep0.fieldnames = ["_Age", "PatientName", "AccessionNumber"]

    for i in range(10):

        tags = {
            "PatientName": "Subject {}".format(i),
            "AccessionNumber": "Study {}".format(i)
        }

        meta = {
            "Age": 20+i
        }

        ep0.dixels.add(Dixel(tags=tags, meta=meta))

    ep0.write()

    ep1 = CsvFile(fp=fp)
    ep1.read()
    d = ep1.dixels.pop()

    logging.debug(d)

    assert( d.meta['Age']>="20" )
    assert( d.tags['PatientName'].startswith("Subject"))

    logging.debug(ep1.fieldnames)

    ep2 = CsvFile(fp=fp)
    ep2.fieldnames = ['_ShamID', '_ShamBirthDate', '_ShamAccessionNumber', 'PatientName', 'AccessionNumber']

    ShamDixel.REFERENCE_DATE = date(year=2018, month=1, day=1)
    for d in ep0.dixels:
        logging.debug(d)
        ep2.dixels.add( ShamDixel.from_dixel(d) )

    ep2.write()

    ep2.fieldnames = "ALL"
    ep2.write()

    os.remove(fp)


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_csv(Path("/Users/derek/tmp"))