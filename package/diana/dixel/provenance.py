import attr
import json
import logging
from datetime import datetime
from cryptography.fernet import Fernet
from crud.abc import Serializable


def mk_time(value):
    if isinstance(value, datetime) or value is None:
        return value
    try:
        dt = datetime.fromisoformat(value)
        return dt
    except:
        logging.warning("Failed to parse dt string")


@attr.s(auto_attribs=True)
class Provenance(Serializable):

    timestamp: datetime = attr.ib(factory=datetime.now, converter=mk_time)
    institution: str = ""
    trial: str = ""
    original_patient_id: str = ""
    original_accession_number: str = ""
    original_study_dt: datetime = attr.ib(default=None, converter=mk_time)

    @classmethod
    def from_token(cls, e, fkey):
        s = Fernet(fkey).decrypt(e)
        d = json.loads(s.decode("utf8"))
        p = cls.Factory.create(**d)
        return p

    def to_token(self, fkey):
        s = self.json()
        e = Fernet(fkey).encrypt(s.encode("utf8"))
        return e
