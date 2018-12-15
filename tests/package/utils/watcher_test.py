from enum import Enum
import logging
from datetime import datetime
import attr
from diana.utils.endpoint import ObservableMixin, Watcher, Event, Trigger

from interruptingcow import timeout

class MockEventTypes(Enum):
    THIS = "this"
    THAT = "that"

@attr.s(cmp=False, hash=None)
class MockObservable(ObservableMixin):

    def changes(self):
        logging.debug("Returning changes")
        return [Event(evtype=MockEventTypes.THIS,
                      source_id=self.uuid,
                      data="THIS at {}".format(datetime.now().isoformat())),
                Event(evtype=MockEventTypes.THAT,
                      source_id=self.uuid,
                      data="THAT at {}".format(datetime.now().isoformat()))
                ]

    def say(self, data):
        print(data)


def test_single_trigger(capsys):

    print("Starting single")

    obs = MockObservable()
    watcher = Watcher()

    trigger0 = Trigger(
        evtype=MockEventTypes.THIS,
        source=obs,
        action=obs.say
    )

    watcher.add_trigger(trigger0)

    try:
        with timeout(3):
            watcher.run()
    except:
        watcher.stop()

    if capsys:
        captured = capsys.readouterr()
        assert "THIS" in captured.out
        assert "THAT" not in captured.out



def test_double_trigger(capsys):

    print("Starting double")

    obs = MockObservable()
    watcher = Watcher()

    trigger0 = Trigger(
        evtype=MockEventTypes.THIS,
        source=obs,
        action=obs.say
    )

    trigger1 = Trigger(
        evtype=MockEventTypes.THAT,
        source=obs,
        action=obs.say
    )

    watcher.add_trigger(trigger0)
    watcher.add_trigger(trigger1)

    try:
        with timeout(3):
            watcher.run()
    except:
        watcher.stop()

    if capsys:
        captured = capsys.readouterr()
        assert "THIS" in captured.out
        assert "THAT" in captured.out


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_single_trigger(None)
    test_double_trigger(None)