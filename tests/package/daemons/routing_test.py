import logging
from interruptingcow import timeout
from diana.daemons import mk_route
from diana.utils.dicom import DicomEventType
from diana.utils.endpoint import Watcher
from test_utils import MockObservable  # Make instantiable

sample_observations = [
    (1, DicomEventType.INSTANCE_ADDED, "first event (INSTANCE)"),
    (1, DicomEventType.SERIES_ADDED, "second event (SERIES)"),
    (2, DicomEventType.INSTANCE_ADDED, "third event (INSTANCE)"),
    (2, DicomEventType.SERIES_ADDED, "fourth event (SERIES)"),
    (3, DicomEventType.INSTANCE_ADDED, "fifth event (INSTANCE)"),
    (3, DicomEventType.SERIES_ADDED, "sixth event (SERIES)"),
]

def test_single_route(capsys):

    print("Starting single")

    watcher = Watcher(action_interval=0.5)

    source_desc = {"ctype": "MockObservable", "polling_interval": 0.5}

    tr = mk_route("say_instances", source_desc=source_desc)
    tr.source.observations = sample_observations

    watcher.add_trigger(tr)

    try:
        with timeout(5):
            watcher.run()
    except:
        watcher.stop()

    if capsys:
        captured = capsys.readouterr()
        assert "INSTANCE" in captured.out
        assert "SERIES" not in captured.out


def test_double_route(capsys):

    print("Starting tripple")

    watcher = Watcher(action_interval=0.5)

    source_desc = {"ctype": "MockObservable", "polling_interval": 0.5}

    tr0 = mk_route("say_instances", source_desc=source_desc)
    tr1 = mk_route("say_hello_instances", source_desc=source_desc)
    tr2 = mk_route("say_series", source_desc=source_desc)

    tr2.source.observations = sample_observations

    watcher.add_trigger(tr0)
    watcher.add_trigger(tr1)
    watcher.add_trigger(tr2)

    try:
        with timeout(5):
            watcher.run()
    except:
        watcher.stop()

    if capsys:
        captured = capsys.readouterr()
        assert "INSTANCE" in captured.out
        assert "hello" in captured.out
        assert "SERIES" in captured.out



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_double_route(None)