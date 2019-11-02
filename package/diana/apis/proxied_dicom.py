from typing import Mapping, Union
from datetime import datetime, timedelta
from functools import partial
from pprint import pformat
import time
import logging
import attr
from crud.abc import Endpoint, Serializable
from crud.exceptions import GatewayConnectionError
from ..utils.dicom import DicomLevel, dicom_date, dicom_time
from ..utils import FuncByDates
from . import Orthanc
from ..dixel import Dixel, DixelView

FIND_SETTLE_TIME = 0.3


@attr.s
class ProxiedDicom(Endpoint, Serializable):

    name = attr.ib( default="ProxiedDicom" )
    proxy_desc = attr.ib( factory=dict )
    proxy_domain = attr.ib( type=str, default="remote" )

    proxy = attr.ib( init=False )
    @proxy.default
    def setup_proxy(self):
        return Orthanc(**self.proxy_desc)

    def find(self, item: Union[Mapping, Dixel], level=DicomLevel.STUDIES,
             retrieve: bool=False, **kwargs):
        return self.proxy.rfind(item,
                                level=level,
                                domain=self.proxy_domain,
                                retrieve=retrieve)

    def get(self, item: Union[str, Dixel], level=DicomLevel.STUDIES,
            view=DixelView.TAGS):
        if not self.exists(item, level=level):
            self.find(item, level=level, retrieve=True)
            time.sleep(FIND_SETTLE_TIME)
        return self.proxy.get(item, level=level, view=view)

    def anonymize(self, item: Union[str, Dixel], level=DicomLevel.STUDIES):
        if not self.exists(item, level=level):
            self.find(item, level=level, retrieve=True)
            time.sleep(FIND_SETTLE_TIME)
        return self.proxy.anonymize(item, level=level)

    def delete(self, item: Union[str, Dixel], level=DicomLevel.STUDIES):
        if self.exists(item, level):
            self.proxy.delete(item, level)

    def exists(self, item, level=DicomLevel.STUDIES):
        return self.proxy.exists(item, level=level)

    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("Check")

        try:
            return self.proxy.gateway.recho(self.proxy_domain) is not None
        except GatewayConnectionError as e:
            logger.warning("Failed to connect to Proxied Endpoint")
            logger.error(type(e))
            logger.error(e)
            return False


    def iter_query_by_date(self, q: Mapping,
                           start: datetime, stop: datetime, step: timedelta):

        def qdt(q, start: datetime, stop: datetime):
            if not q:
                q = {}
            _start = min(start, stop)
            _end = max(start, stop)
            if _start.date() != _end.date():
                q['StudyDate'] = "{}-{}".format(dicom_date(_start), dicom_date(_end))
            else:
                q['StudyDate'] = "{}".format(dicom_date(_start))
            q['StudyTime'] = "{}-{}".format(dicom_time(_start), dicom_time(_end))
            return q

        func = partial(qdt, q)
        _gen = FuncByDates(func, start, stop, step)

        for q in _gen:
            logging.debug(pformat(q))
            cache = self.find(q)

            for item in cache:
                yield item

ProxiedDicom.register()
