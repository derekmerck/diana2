import logging, time
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable
import attr
from . import ObservableMixin, Event

@attr.s
class Trigger(object):
    evtype = attr.ib(type=Enum)
    source = attr.ib(type=ObservableMixin)
    action = attr.ib(type=Callable)

    @property
    def source_id(self):
        return self.source.uuid


@attr.s
class Watcher(object):
    sources = attr.ib( factory=dict, init=False )
    triggers = attr.ib( factory=dict, init=False  )
    action_interval = attr.ib( default=1.0 )

    def add_trigger(self, trigger: Trigger):
        self.sources[trigger.source_id] = trigger.source
        self.triggers[(trigger.source_id, trigger.evtype)] = trigger.action

    def fire(self, event: Event):
        func = self.triggers.get((event.source_id, event.evtype))
        if func:
            return func(event.data)

    def stop(self):
        for source in self.sources.values():
            source.proc.terminate()

    def run(self):

        for source in self.sources.values():
            source.poll_events()

        while True:
            # self.logger.debug("Checking queues")

            tic = datetime.now()

            for source in self.sources.values():
                while not source.event_queue.empty():
                    event = source.event_queue.get()
                    self.fire(event)

            toc = datetime.now()
            if toc - tic < timedelta(seconds=self.action_interval):
                time.sleep(self.action_interval - (toc - tic).seconds)
