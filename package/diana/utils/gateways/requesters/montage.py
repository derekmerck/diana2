# Diana-agnostic API for Montage, with no endpoint or dixel dependencies

import logging, csv
from pathlib import Path
from typing import Mapping
import attr
from bs4 import BeautifulSoup
from .requester import Requester


bp_desc_lut = {
    "UpperExtremity": ["arm", "shoulder", "elbow", "wrist", "hand", "finger",
                       "clavicle", "radius", "humerus", "ulna", "ac jt", "bone age"],
    "LowerExtremity": ["leg", "hip", "knee", "ankle", "foot", "toe",
                       "femur", "tibia", "fibula", "bone length"],
    "Head":  ["head", "eye", "skull", "nose", "brain", "panorex"],
    "Chest": ["chest", "rib", "lung", "scapula"],
    "Abdomen": ["abdomen", "abd"],
    "Pelvis": ["pelvis"],
    "Spine":  ["spine", "neck", "flexion", "scoliosis", "sacrum"],
    "Full Body": ["single film", "panscan"],
    "Foreign Body": ["foreign body"]
}

@attr.s
class Montage(Requester):

    name = attr.ib(default="MontageGateway")
    user = attr.ib(default="montage")
    path = attr.ib( default="apis/v1")
    index = attr.ib( default="rad" )

    def find(self, query: Mapping, index: str=None):
        logger = logging.getLogger(self.name)
        logger.debug("Searching montage")

        index = index or self.index

        resource = "index/{}/search/".format(index)
        return self._get(resource, params={**query, 'format': 'json'})

    bp_lut = {}
    @classmethod
    def init_bp_lut(cls, fp: Path):
        with open(fp) as f:
            reader = csv.DictReader(f)
            for item in reader:
                cls.bp_lut[item["ProcedureCode"]] = item["BodyPartName"]

    @classmethod
    def bp_from(cls, code, desc):
        body_part = cls.bp_lut.get(code)
        if body_part:
            return body_part
        desc = desc.lower()
        for body_part, v in bp_desc_lut.items():
            for label in v:
                if label in desc:
                    cls.bp_lut[code] = body_part
                    return body_part

    cpt_lut = {}
    @classmethod
    def cpt_from(cls, codes):
        results = []
        for c in codes:
            label = cls.cpt_lut.get(c)
            if not label:
                resource = '/api/v1/cptcode/{}'.format(c)
                r = cls._get(resource)
                label = r['label']
                results.append(label)
        return results

    mod_lut = {
        "XR": 95,
        "CR": 100,
        "CT": 4,
        "XA": 66
    }
    @classmethod
    def mod_value(cls, label):
        value = cls.mod_lut.get(label)
        if value:
            return value
        else:
            raise ValueError

    @classmethod
    def clean_text(cls, text):
        soup = BeautifulSoup(text, features="html.parser")
        lines = soup.findAll(text=True)

        # Look at every line, replace blanks and \r with \n
        for i, item in enumerate(lines):
            item = item.replace("\r", "\n")
            if item == ' ':
                 item = "\n"
            lines[i] = item

        result = "".join(lines)
        return result