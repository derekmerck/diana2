from enum import IntEnum
import logging
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

# Max results to review for a given query
MONTAGE_RESULT_LIMIT = 600
# Max results to return _per page_ for a given query
MONTAGE_RESULT_INCR = 200

@attr.s
class Montage(Requester):
    """
    Diana-agnostic API for Montage, with no endpoint or dixel dependencies

    There is no montage-sdk for Python afaik; this gateway provides a minimal
    functionality to 'find' events and collect some additional metadata about
    body part and cpt code.
    """

    name = attr.ib(default="MontageGateway")
    user = attr.ib(default="montage")
    path = attr.ib( default="apis/v1")
    index = attr.ib( default="rad" )

    def find(self, query: Mapping, index: str=None) -> list:
        logger = logging.getLogger(self.name)
        logger.debug("Searching montage")

        index = index or self.index

        offset = 0
        incr = MONTAGE_RESULT_INCR

        resource = "index/{}/search/".format(index)
        r = self._get(resource, params={**query,
                                        'offset': offset,
                                        'limit': incr,
                                        'format': 'json'})

        total = min( MONTAGE_RESULT_LIMIT, r['meta']['total_count'] )
        results = r['objects']

        logging.debug(r['meta'])

        while total > offset + incr:
            offset += incr
            r = self._get(resource, params={**query,
                                            'offset': offset,
                                            'limit': incr,
                                            'format': 'json'})
            results += r['objects']
            # logging.debug(r['objects'])

        # logging.debug(results)
        return results

    # ----------------
    # Metadata functions
    # ----------------

    _bp_lut = {}
    def lookup_body_part(self, montage_cpts: list) -> list:
        """Build up cached lookup tables for body part from exam code."""
        results = []
        for mc in montage_cpts:
            labels = self._bp_lut.get(mc)
            if not labels:

                labels = []

                cpt_resource = "cptcode/{}".format(mc)
                r = self._get(cpt_resource)
                # logging.debug(r)
                anatomies = r['anatomies']

                for a in anatomies:

                    val = a.split('/')[-2]
                    anat_resource = "anatomy/{}".format(val)

                    def find_parent(_resource):
                        rr = self._get(_resource)
                        if rr['parent']:
                            val = rr['parent'].split('/')[-2]
                            __resource = "anatomy/{}".format(val)
                            return find_parent(__resource)
                        else:
                            # logging.debug(rr)
                            return rr['label']

                    label = find_parent(anat_resource)
                    if label not in labels:
                        labels.append(label)

                self._bp_lut[mc] = labels

                # logging.debug(labels)

            # Now we have an array of anatomy labels

            for label in labels:
                if label not in results:
                    results.append(label)

        return results

    _cpt_lut = {}
    def lookup_cpts(self, montage_cpts: list) -> list:
        """Build up cached lookup table for cpt codes from exam code."""

        results = []
        for mc in montage_cpts:
            label = self._cpt_lut.get(mc)
            if not label:
                resource = "cptcode/{}".format(mc)
                r = self._get(resource)
                # logging.debug(r)
                label = r['code']
                self._cpt_lut[mc] = label
            results.append(label)
        return results

    @classmethod
    def clean_text(cls, text):
        """Clean up text from the RIH report templates.
        Recent variants are returned with \\r indicators, older variants are
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
