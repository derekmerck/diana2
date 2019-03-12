
from typing import Iterator
import attr

from ..utils.endpoint import Endpoint


@attr.s
class Collector(object):

    source = attr.ib(type=Endpoint)
    dest = attr.ib(type=Endpoint)

    threads = attr.ib(default=0)
    pause = attr.ib(default=0.1)

    dryrun = attr.ib(default=False)

    def run(self, worklist: Iterator):
        for item in worklist:
            _item = self.source.get(item, dryrun=self.dryrun)
            self.dest.put(_item)
