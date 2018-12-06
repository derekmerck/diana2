from hashlib import sha1
from typing import Union
from datetime import date, timedelta
from dateutil import parser as DateTimeParser
import random
import logging
import re
from enum import Enum
import base64
from pathlib import Path


def dicom_name(names: list) -> str:
    s = "^".join(names).upper()
    return s

def dicom_date(dt: date) -> str:
    s = dt.strftime("%Y%m%d")
    return s


# New dob is within 3 months
DOB_DISTANCE = 90

class GUIDGender(Enum):

    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"


class GUIDMint(object):

    @classmethod
    def get_hash(cls,
                 name: str,
                 dob: date=None,
                 age: int=None,
                 reference_date: date = None,
                 gender = GUIDGender.UNKNOWN) -> [sha1, date]:
        """Use the study date as a reference date for reproducible dob given age only"""

        logger = logging.getLogger("GUIDMint")

        def handle_name(name: str) -> str:
            names = name.lower()
            names = re.split('[^a-z]', names)
            names = [x for x in names if x]
            names.sort()
            names = "-".join(names)
            return names

        def handle_dob(dob: date=None, age: int=0, reference_date: date=None) -> date:

            if not dob and not age:
                raise KeyError("Minting a GUID requires either a date or an age")
            if not dob:
                if not reference_date:
                    reference_date = date.today()
                    logger.warning("Creating non-reproducible GUID using current date")
                dob = reference_date - timedelta(days = age*365.25)

            return dob

        dob = handle_dob(dob, age, reference_date)

        key = "|".join([handle_name(name),
                        dob.isoformat(),
                        gender.value])
        logger.debug("key: {}".format(key))

        random.seed(key)
        dob_offset = random.randint(-DOB_DISTANCE, DOB_DISTANCE)
        new_dob = dob + timedelta(days=dob_offset)
        logger.debug(new_dob.isoformat())

        h = sha1(key.encode("UTF-8"))
        logger.debug(h.digest())

        return h, new_dob

    @classmethod
    def get_id(cls, h: sha1) -> str:

        logger = logging.getLogger("GUIDMint")

        s = base64.b32encode(h.digest()).decode("UTF-8")
        while not s[0:2].isalpha():
            h = sha1(h.digest())
            s = base64.b32encode(h.digest()).decode("UTF-8")
        logger.debug(s)
        return s

    names = {}

    @classmethod
    def get_name(cls, id: str, gender=GUIDGender.UNKNOWN) -> list:

        logger = logging.getLogger("GUIDMint")
        random.seed(id+str(gender))

        def init_name_banks():
            here = Path(__file__).parent

            fns = [("dist.all.last.txt", "last"),
                   ("dist.female.first.txt", "female"),
                   ("dist.male.first.txt", "male")]

            for fn, var in fns:

                with open(here/'us_census'/fn) as f:
                    data = []
                    lines = f.readlines()
                    for line in lines:
                        word = line.split()[0]
                        data.append(word)

                    data.sort()
                    cls.names[var] = data

            # logging.debug(var)

        if not cls.names:
            init_name_banks()

            # logging.debug(cls.names)

        initial = id[0]
        candidates = cls.names["last"]
        candidates = list(filter(lambda n: n.startswith(initial), candidates))
        last = random.choice(candidates)
        logger.debug(last)

        initial = id[1]
        if gender == GUIDGender.FEMALE:
            candidates = cls.names["female"]
        else:
            candidates = cls.names["male"]

        candidates = list(filter(lambda n: n.startswith(initial), candidates))
        first = random.choice(candidates)

        logger.debug(first)

        middle = id[2]

        return [last, first, middle]

    @classmethod
    def get_sham_id(cls, name: str,
                    dob: Union[date, str]=None,
                    age: int=None,
                    reference_date: date=None,
                    gender="U"):

        if isinstance(dob, str):
            P = DateTimeParser()
            dob = P.parse(dob).date()

        gender = GUIDGender(gender)

        _hash, _dob = M.get_hash(name, dob=dob, age=age, gender=gender)
        _id = M.get_id(_hash)
        _name = M.get_name(_id, gender)

        return _id, dicom_name(_name), dicom_date(_dob)





logging.basicConfig(level=logging.DEBUG)


M = GUIDMint()

s = "HELLO^THERE^ME^^"
age = 10

logging.debug( M.get_sham_id(s, age=age))
