from itertools import count
from typing import Iterable
from datetime import datetime, timedelta
import time
from multiprocessing import Process, Queue
from enum import Enum
import attr
from . import Serializable


@attr.s
class Event(object):

    n_events = count(0)
    evid = attr.ib( init=False, factory=n_events.__next__ )
    source_id = attr.ib( type=str )
    evtype = attr.ib( type=Enum )
    data = attr.ib( default=None )
    timestamp = attr.ib( init=False, factory=datetime.now )
    source = attr.ib( init=False, default=None )

    def __str__(self):
        return "evid {} : {} : {} : data {}".format(self.evid,
                                          self.source_id,
                                          self.evtype,
                                          self.data)

@attr.s(cmp=False, hash=None)
class ObservableMixin(Serializable):

    event_queue = attr.ib( init=False, factory=Queue )
    polling_interval = attr.ib(default=1.0)
    proc = attr.ib( init=False, type=Process, default=None )

    # Returns iterable of Event objects
    def changes(self, **kwargs) -> Iterable[Event]:
        raise NotImplementedError

    def poll_events(self):

        def poll():
            while True:

                tic = datetime.now()
                events = self.changes()

                if events:
                    for event in events:
                        self.event_queue.put(event)

                toc = datetime.now()
                if toc-tic < timedelta(seconds=self.polling_interval):
                    time.sleep(self.polling_interval - (toc-tic).seconds)

        self.proc = Process(target=poll)
        self.proc.start()