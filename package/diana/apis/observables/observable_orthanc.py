import attr
from diana.apis import Orthanc
from diana.utils.endpoint import Event, ObservableMixin
from diana.utils.dicom import DicomEvent

@attr.s
class ObservableOrthanc(Orthanc, ObservableMixin):

    current_change = attr.ib(init=False, default=0)

    def changes(self, **kwargs):

        done = False
        event_queue = []

        while not done:
            r = self.gateway.changes(current=self.current_change)
            for change in r['Changes']:
                if change['ChangeType'] == 'NewInstance':
                    e = Event(
                        evtype=DicomEvent.INSTANCE_ADDED,
                        source_id=self.uuid,
                        data={"oid": change['ID']}
                    )
                    event_queue.append(e)
                elif change['ChangeType'] == 'StableSeries':
                    e = Event(
                        evtype=DicomEvent.SERIES_ADDED,
                        source_id=self.uuid,
                        data={"oid": change['ID']}
                    )
                    event_queue.append(e)
                elif change['ChangeType'] == 'StableStudy':
                    e = Event(
                        evtype=DicomEvent.STUDY_ADDED,
                        source_id=self.uuid,
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
