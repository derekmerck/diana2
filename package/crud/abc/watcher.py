import logging, time
from abc import ABC
from itertools import count
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable
import attr
from .observable import ObservableMixin, Event


@attr.s
class Trigger(object):
    n_items = count(0)
    tgid = attr.ib(init=False, factory=n_items.__next__)
    evtype = attr.ib(type=Enum)
    source = attr.ib(type=ObservableMixin)
    action = attr.ib(type=Callable)

    @property
    def source_id(self):
        return self.source.epid

    def __str__(self):
        return "tgid {} : {} : {} : action {}".format(self.tgid,
                                          self.source_id,
                                          self.evtype,
                                          self.action)


@attr.s
class Watcher(ABC):
    """
    Generic event handler.  Setup is through Trigger objects that map sources and
    event types to a partial function call.  Events then arrive via event_queues
    from Observable sources.

    Any CRUD endpoint that implements "Observable" is an eligible source.
    """

    sources = attr.ib( factory=dict, init=False )
    triggers = attr.ib( factory=dict, init=False  )
    action_interval = attr.ib( default=1.0 )

    def add_trigger(self, trigger: Trigger):
        self.sources[trigger.source_id] = trigger.source
        self.triggers[(trigger.source_id, trigger.evtype, trigger.tgid)] = trigger.action

    def fire(self, event: Event):
        matches = {
            k: v for (k,v) in self.triggers.items() if k[0] == event.source_id and
                                                       k[1] == event.evtype
            }
        for func in matches.values():
            func(event.data)

    def stop(self):
        if self.sources:
            for source in self.sources.values():
                if hasattr(source.proc, "terminate"):
                    source.proc.terminate()

    def __del__(self):
        print("Destroying watcher")
        self.stop()

    def run(self):

        logger = logging.getLogger("Watcher")
        logger.debug("Running")

        if self.sources:
            for source in self.sources.values():
                source.poll_events()

        while True:
            logger.debug("Checking queues")

            tic = datetime.now()

            if self.sources:
                for source in self.sources.values():
                    while not source.event_queue.empty():
                        event = source.event_queue.get()
                        self.fire(event)

            toc = datetime.now()
            if toc - tic < timedelta(seconds=self.action_interval):
                time.sleep(self.action_interval - (toc - tic).seconds)
