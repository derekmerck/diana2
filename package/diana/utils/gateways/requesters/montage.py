# Diana-agnostic API for Montage, with no endpoint or dixel dependencies

import logging
from typing import Mapping
import attr
from bs4 import BeautifulSoup
from .requester import Requester

def montage_text_cleaner(text):
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

        resource = "index/{}/search".format(index)
        return self._get(resource, params={**query, 'format': 'json'})
