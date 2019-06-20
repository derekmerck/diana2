import pickle
import string
import logging
from pathlib import Path
import attr
from .. import Orthanc
from ...utils.endpoint import Event, ObservableMixin
from ...utils.dicom import DicomEventType


def slugify(s):
    safechars = string.ascii_letters + string.digits + " -_."
    s = "".join( filter(lambda c: c in safechars, s) )
    return s


@attr.s
class ObservableOrthanc(Orthanc, ObservableMixin):
    """
    Orthanc service that implements a DicomEvents "changes" function for polling.
    """

    name = attr.ib(default="ObsOrthanc")

    persist_file = attr.ib(type=Path, convert=Path)
    @persist_file.default
    def set_persist_file(self):
        return "/tmp/diana-" + slugify(self.gateway.base_url) + "-changes.pik"

    _current_change = attr.ib(type=int, convert=int, init=False)
    @_current_change.default
    def set_current_change(self):
        if self.persist_file.is_file():
            try:
                with self.persist_file.open("rb") as f:
                    current_change = pickle.load(f)
                    return current_change
            except:
                logging.error("Unable to read changes file, resetting to 0")
                return 0
        else:
            return 0

    def persist_current_change(self):
        with self.persist_file.open("wb") as f:
            pickle.dump(self._current_change, f)

    def persist_last_change(self):

        done = False
        while not done:
            r = self.gateway.changes(current=self._current_change, limit=10000)
            self._current_change = r['Last']
            done = r['Done']

        logger = logging.getLogger(self.name)
        logger.info("Last change was {}".format(self._current_change))
        self.persist_current_change()

    def changes(self, **kwargs):

        done = False
        event_queue = []

        while not done:
            r = self.gateway.changes(current=self._current_change)
            for change in r['Changes']:
                if change['ChangeType'] == 'NewInstance':
                    e = Event(
                        evtype=DicomEventType.INSTANCE_ADDED,
                        source_id=self.epid,
                        data={"oid": change['ID']}
                    )
                    event_queue.append(e)
                    logging.debug("Made a new instance event for source: {}".format(self.epid))
                    logging.debug(self)
                elif change['ChangeType'] == 'StableSeries':
                    e = Event(
                        evtype=DicomEventType.SERIES_ADDED,
                        source_id=self.epid,
                        data={"oid": change['ID']}
                    )
                    event_queue.append(e)
                elif change['ChangeType'] == 'StableStudy':
                    e = Event(
                        evtype=DicomEventType.STUDY_ADDED,
                        source_id=self.epid,
                        data={"oid": change['ID']}
                    )
                    event_queue.append(e)
                else:
                    logging.debug("Found unhandled change type: {}".format( change['ChangeType']))
                    pass
            self._current_change = r['Last']
            done = r['Done']

        self.persist_current_change()

        if event_queue:
            # self.logger.debug("Found {} Orthanc changes for {}".format(len(event_queue), self.location))
            return event_queue

