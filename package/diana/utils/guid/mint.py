from enum import Enum
from hashlib import sha1
from typing import Union
from datetime import date, timedelta
import random
import logging
import re
import base64
from pathlib import Path
from dateutil import parser as DateTimeParser
from ..dicom import dicom_name, dicom_date

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

        def handle_dob(dob: date=None, age: int=None, reference_date: date=None) -> date:

            if not dob and not age:
                raise KeyError("Minting a GUID requires either a date or an age")
            if not dob:
                if not reference_date:
                    reference_date = date.today()
                    logger.warning("Creating non-reproducible GUID using current date")
                logger.info("Inferring  date of birth given age and ref")
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
        while not s[0:3].isalpha():
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
    def get_sham_id(cls,
                    name: str,
                    dob: Union[date, str]=None,
                    age: int=None,
                    reference_date: Union[date,str]=None,
                    gender="U"):

        if isinstance(dob, str):
            dob = DateTimeParser.parse(dob).date()

        if isinstance(reference_date, str):
            reference_date = DateTimeParser.parse(reference_date).date()

        gender = GUIDGender(gender)

        _hash, _dob = cls.get_hash(name,
                                   dob=dob,
                                   age=age,
                                   reference_date=reference_date,
                                   gender=gender)
        _id = cls.get_id(_hash)
        _name = cls.get_name(_id, gender)

        return _id, dicom_name(_name), dicom_date(_dob)


