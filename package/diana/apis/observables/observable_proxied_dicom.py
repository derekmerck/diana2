from datetime import datetime, timedelta
from collections import deque
import attr
from diana.apis import ProxiedDicom
from diana.utils.endpoint import Event, ObservableMixin
from diana.utils.dicom import DicomEventType, DicomLevel, dicom_date, dicom_time

@attr.s
class ObservableProxiedDicom(ProxiedDicom, ObservableMixin):
    """
    ProxiedDicom service that implements a DicomEvents "changes" function
    for polling.  Restricted to observing recent events, from now to qperiod
    seconds in the past.

    It is intended that qperiod >> polling_interval to avoid missing events
    that may have delivered slowly or would be missed by keeping a near-0
    overlap between polling and query windows.  A history queue tracks the n
    most recently observed events and suppresses multiple notifications.
    """

    name = attr.ib(default="ObsPrxDcm")
    query = attr.ib(factory=dict)
    qlevel = attr.ib(default=DicomLevel.STUDIES)
    qperiod = attr.ib( default=300, convert=int)

    history = attr.ib(init=False)
    history_len = attr.ib(default=200)
    @history.default
    def setup_history(self):
        return deque(maxlen=self.history_len)

    def changes(self, **kwargs):

        def mk_recent_query():

            begin = datetime.now()
            d0 = dicom_date(begin)
            t0 = dicom_time(begin)

            end = begin - timedelta(seconds=self.qperiod)
            d1 = dicom_date(end)
            t1 = dicom_time(end)

            q = {}
            q.update(self.query)
            q['StudyDate'] = d0 if d0==d1 else "{}-{}".format(d0, d1)
            q['StudyTime'] = "{}-{}".format(t0, t1)

            return q

        ret = self.find(query=mk_recent_query(), level=self.qlevel)

        event_queue = []
        for item in ret:

            if self.qlevel == DicomLevel.STUDIES:
                match_key = item['StudyInstanceUID']
                evtype = DicomEventType.STUDY_ADDED
            elif self.qlevel == DicomLevel.SERIES:
                match_key = item['SeriesInstanceUID']
                evtype = DicomEventType.SERIES_ADDED
            else:
                raise ValueError

            if match_key in self.history:
                continue
            else:
                self.history.push(match_key)
                e = Event(
                    evtype=evtype,
                    source_id=self.epid,
                    data=item
                )
                event_queue.append(e)

        if event_queue:
            return event_queue




