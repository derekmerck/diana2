import attr
from .. import Orthanc
from ...utils.endpoint import Event, ObservableMixin
from ...utils.dicom import DicomEventType

# TODO: Add a persistent entry for "current_change", file with number, pickled state, redis...

@attr.s
class ObservableOrthanc(Orthanc, ObservableMixin):
    """
    Orthanc service that implements a DicomEvents "changes" function for polling.
    """

    name = attr.ib(default="ObsOrthanc")
    current_change = attr.ib(init=False, default=0)

    def changes(self, **kwargs):

        done = False
        event_queue = []

        while not done:
            r = self.gateway.changes(current=self.current_change)
            for change in r['Changes']:
                if change['ChangeType'] == 'NewInstance':
                    e = Event(
                        evtype=DicomEventType.INSTANCE_ADDED,
                        source_id=self.epid,
                        data={"oid": change['ID']}
                    )
                    event_queue.append(e)
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
                    # self.logger.debug("Found unhandled change type: {}".format( change['ChangeType']))
                    pass
            self.current_change = r['Last']
            done = r['Done']

        if event_queue:
            # self.logger.debug("Found {} Orthanc changes for {}".format(len(event_queue), self.location))
            return event_queue
