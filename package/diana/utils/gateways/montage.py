# Diana-agnostic API for Montage, with no endpoint or dixel dependencies

import logging
from typing import Mapping
import attr
from .requester import Requester


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