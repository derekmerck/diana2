import logging
from datetime import datetime, timedelta
from enum import Enum
import attr
from diana.utils.endpoint import Serializable, ObservableMixin, Event

class MockEventType(Enum):
    THIS = "this"
    THAT = "that"

#: Observation format is (delay, event type, data payload)
sample_observations = [
    (1, MockEventType.THIS, "first event (THIS)"),
    (1, MockEventType.THAT, "second event (THAT)"),
    (2, MockEventType.THIS, "third event (THIS)"),
    (2, MockEventType.THAT, "fourth event (THAT)"),
    (3, MockEventType.THIS, "fifth event (THIS)"),
    (3, MockEventType.THAT, "sixth event (THAT)"),
]

@attr.s(cmp=False, hash=None)
class MockObservable(Serializable, ObservableMixin):
    """A minimal implementation of the Observable Mixin that can be scripted for testing."""

    observations = attr.ib(init=False, type=list, default=sample_observations, repr=False)
    start_time = attr.ib(init=False, factory=datetime.now)
    polling_interval = 0.5

    def changes(self):

        td = datetime.now() - self.start_time

        result = []
        while self.observations and timedelta( seconds=self.observations[0][0] ) < td:
            item = self.observations.pop(0)
            event = Event(
                source_id=self.epid,
                evtype=item[1],
                data=item[2]
            )
            result.append(event)

        if result:
            logging.debug("Found changes")
            return result
        else:
            logging.debug("No changes")


    def say(self, data):
        print(data)

Serializable.Factory.registry["MockObservable"] = MockObservable
