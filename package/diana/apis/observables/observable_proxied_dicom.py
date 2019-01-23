import logging
from datetime import datetime, timedelta
from collections import deque
import attr
from .. import ProxiedDicom
from ...utils.endpoint import Event, ObservableMixin
from ...utils.dicom import DicomEventType, DicomLevel, dicom_date, dicom_time

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
    polling_interval = attr.ib( default=180.0, converter=int )  #: Poll every 3 mins by default
    query = attr.ib()
    @query.default
    def setup_query(self):
        return { "AccessionNumber": "",
                 "StudyInstanceUID": "",
                 "PatientName": "",
                 "PatientID": "",
                 "PatientBirthDate": ""}
    qlevel = attr.ib(default=DicomLevel.STUDIES, converter=DicomLevel.from_label)
    qperiod = attr.ib( default=600, converter=int)  #: Check last 10 mins by default

    history_len = attr.ib(default=200)              #: Set to at least 10 mins of studies
    history = attr.ib(init=False)
    @history.default
    def setup_history(self):
        return deque(maxlen=self.history_len)

    def changes(self, **kwargs):
        logger = logging.getLogger(self.name)

        def mk_recent_query():

            latest = datetime.now()
            dl = dicom_date(latest)
            tl = dicom_time(latest)

            earliest = latest - timedelta(seconds=self.qperiod)
            de = dicom_date(earliest)
            te = dicom_time(earliest)

            q = {}
            q.update(self.query)
            if self.qlevel == DicomLevel.SERIES:
                q['SeriesInstanceUID'] = ""
                q['SeriesDate'] = ""
                q['SeriesTime'] = ""
            q['StudyDate'] = de if de==dl else "{}-{}".format(de, dl)
            q['StudyTime'] = "{}-{}".format(te, tl)

            return q

        q = mk_recent_query()
        logger.debug(q)
        ret = self.find(query=q, level=self.qlevel)
        if not ret:
            return

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
                self.history.append(match_key)
                e = Event(
                    evtype=evtype,
                    source_id=self.epid,
                    data=item
                )
                event_queue.append(e)

        if event_queue:
            return event_queue




