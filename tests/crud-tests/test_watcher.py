import logging
from interruptingcow import timeout
from utils import MockObservable, MockEventType
from crud.abc import Watcher, Trigger


def test_single_trigger(capsys):

    print("Starting single")

    obs = MockObservable()
    watcher = Watcher(action_interval=0.5)

    trigger0 = Trigger(
        evtype=MockEventType.THIS,
        source=obs,
        action=obs.say
    )

    watcher.add_trigger(trigger0)

    try:
        with timeout(5):
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
    watcher = Watcher(action_interval=0.5)

    trigger0 = Trigger(
        evtype=MockEventType.THIS,
        source=obs,
        action=obs.say
    )

    trigger1 = Trigger(
        evtype=MockEventType.THAT,
        source=obs,
        action=obs.say
    )

    watcher.add_trigger(trigger0)
    watcher.add_trigger(trigger1)

    try:
        with timeout(5):
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
