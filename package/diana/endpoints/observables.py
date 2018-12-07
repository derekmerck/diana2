import attr
from . import Orthanc, DcmDir
from ..utils.endpoint import Observable, Serializable
from ..utils.dicom import DicomEvent


@attr.s
class ObservableOrthanc(Orthanc, Observable):

    current_change = attr.ib(init=False, default=0)

    def changes(self, **kwargs):

        done = False
        event_queue = []

        while not done:
            r = self.gateway.changes(current=self.current_change)
            for change in r['Changes']:
                if change['ChangeType'] == 'NewInstance':
                    oid = change['ID']
                    event_queue.append((DicomEvent.INSTANCE_ADDED, oid))
                elif change['ChangeType'] == 'StableSeries':
                    oid = change['ID']
                    event_queue.append((DicomEvent.SERIES_ADDED, oid))
                elif change['ChangeType'] == 'StableStudy':
                    oid = change['ID']
                    event_queue.append((DicomEvent.STUDY_ADDED, oid))
                else:
                    # self.logger.debug("Found unhandled change type: {}".format( change['ChangeType']))
                    pass
            self.current_change = r['Last']
            done = r['Done']

        if event_queue:
            # self.logger.debug("Found {} Orthanc changes for {}".format(len(event_queue), self.location))
            return event_queue

Serializable.Factory.register(ObservableOrthanc)


class ObservableDcmDir(DcmDir, Observable):

    def changes(self, **kwargs):
        raise NotImplementedError


Serializable.Factory.register(ObservableDcmDir)
