from abc import ABC
from itertools import count
from typing import Iterable
from datetime import datetime, timedelta
import time
from multiprocessing import Process, Queue
from enum import Enum
import attr


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
class ObservableMixin(ABC):
    """
    API for event polling and changes methods.  Useful for extending the generic
    CRUD endpoint with "changes", so that it can be attended by the watcher class.
    """

    event_queue = attr.ib( init=False, factory=Queue )
    polling_interval = attr.ib(default=1.0, converter=int)
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

    def __del__(self):
        if self.proc:
            self.proc.terminate()

    def say(self, item):
        """Testing callback"""
        print(item)
