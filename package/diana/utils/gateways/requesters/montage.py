# Diana-agnostic API for Montage, with no endpoint or dixel dependencies

# There is no montage-sdk for Python afaik; this gateway provides a minimal
# functionality to 'find' events and collect some additional metadata about
# body part and cpt code.

from enum import IntEnum
import logging, csv, re
from pathlib import Path
from typing import Mapping
import attr
from bs4 import BeautifulSoup
from .requester import Requester


# For RIH
class MontageModality(IntEnum):
    XR = 95
    CR = 100
    CT = 4
    XA = 66

    def __str__(self):
        return str(self.value)

MONTAGE_RESULT_LIMIT = 100

# bp_desc_lut = {
#     "UpperExtremity": ["arm", "shoulder", "elbow", "wrist", "hand", "finger",
#                        "clavicle", "radius", "humerus", "ulna", "ac jt", "bone age"],
#     "LowerExtremity": ["leg", "hip", "knee", "ankle", "foot", "toe",
#                        "femur", "tibia", "fibula", "bone length"],
#     "Head":  ["head", "eye", "skull", "nose", "brain", "panorex"],
#     "Chest": ["chest", "rib", "lung", "scapula"],
#     "Abdomen": ["abdomen", "abd"],
#     "Pelvis": ["pelvis"],
#     "Spine":  ["spine", "neck", "flexion", "scoliosis", "sacrum"],
#     "Full Body": ["single film", "panscan"],
#     "Foreign Body": ["foreign body"]
# }
# body_part = cls.bp_lut.get(code)
# if body_part:
#     return body_part
# desc = desc.lower()
# for body_part, v in bp_desc_lut.items():
#     for label in v:
#         if label in desc:
#             cls.bp_lut[code] = body_part
#             return body_part

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

        offset = 0
        limit = MONTAGE_RESULT_LIMIT

        resource = "index/{}/search/".format(index)
        r = self._get(resource, params={**query,
                                        'offset': offset,
                                        'limit': limit,
                                        'format': 'json'})

        total = r['meta']['total_count']
        results = r['objects']

        logging.debug(r['meta'])

        while total > offset + limit:
            offset += limit
            r = self._get(resource, params={**query,
                                            'offset': offset,
                                            'limit': limit,
                                            'format': 'json'})
            results += r['objects']
            # logging.debug(r['objects'])

        logging.debug(results)
        return results


    # ----------------
    # Metadata functions
    # ----------------

    # Build up cached lookup tables for body part and cpt code from exam code.

    bp_lut = {}
    def lookup_body_part(self, montage_cpts):
        results = []
        for mc in montage_cpts:
            label = self.bp_lut.get(mc)
            if not label:
                resource = "cptcode/{}".format(mc)
                r = self._get(resource)
                # logging.debug(r)
                anatomies = r['anatomies']

                for a in anatomies:

                    val = a.split('/')[-2]
                    resource = "anatomy/{}".format(val)

                    def find_parent(_resource):
                        rr = self._get(_resource)
                        if rr['parent']:
                            val = rr['parent'].split('/')[-2]
                            resource = "anatomy/{}".format(val)
                            return self._get(resource)
                        else:
                            # logging.debug(rr)
                            return rr['label']

                    label = find_parent(resource)

                self.bp_lut[mc] = label

            if label not in results:
                results.append(label)
        return results

    cpt_lut = {}
    def lookup_cpts(self, montage_cpts):
        results = []
        for mc in montage_cpts:
            label = self.cpt_lut.get(mc)
            if not label:
                resource = "cptcode/{}".format(mc)
                r = self._get(resource)
                # logging.debug(r)
                label = r['code']
                self.cpt_lut[mc] = label
            results.append(label)
        return results

    @classmethod
    def clean_text(cls, text):
        """Clean up text from the RIH report templates.
        Recent variants are returned with \r indicators, older variants are
        not, so we insert newlines based on whether the next line is a
        continuation or an obviously new section."""
        soup = BeautifulSoup(text, features="html.parser")
        text = soup.findAll(text=True)

        lines = []
        # Look at every line, replace blanks and \r with \n
        for i in range(len(text)-1):
            item = text[i]
            item = item.replace("\r", "\n")
            if text[i+1][0].isupper() or text[i+1][0].isnumeric():
                item += "\n"
            lines.append(item)
        lines.append(text[-1])

        result = "".join(lines)
        return result
