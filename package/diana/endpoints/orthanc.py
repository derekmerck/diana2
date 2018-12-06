import logging
import hashlib
from typing import Mapping, Union
from diana.dixel.dixel import Dixel
from ..utils import Endpoint, Serializable
from ..utils.gateways import Orthanc as OrthancGateway, OrthancView, GatewayConnectionError
from ..utils.dicom import DicomLevel
import attr


def sham_map(d: Dixel):

    logging.debug(d)

    m = {
        "Replace": {
            "PatientName": d.tags["ShamPatientName"],
            "PatientID": d.tags["ShamPatientID"],
            "PatientBirthDate": d.tags["ShamPatientBirthDate"],
            "AccessionNumber": hashlib.md5( d.tags["AccessionNumber"].encode("UTF-8") ).hexdigest()
            },
        "Keep": [
            "PatientSex",
            'StudyDescription',
            'SeriesDescription',
            'StudyDate',
            'StudyTime'
            ],
        "Force": True
    }
    return m


@attr.s
class Orthanc(Endpoint, Serializable):

    name = attr.ib(default="Orthanc")

    protocol = attr.ib(default="http")
    host = attr.ib(default="localhost")
    port = attr.ib(default=8042)
    path = attr.ib(default=None)
    aet = attr.ib(default="ORTHANC")

    user = attr.ib(default="orthanc")
    password = attr.ib(default="passw0rd!")

    gateway = attr.ib(init=False, type=OrthancGateway, repr=False)

    @gateway.default
    def setup_gateway(self):
        return OrthancGateway(
            name = "OrthancGateway",
            protocol = self.protocol,
            host = self.host,
            port = self.port,
            path = self.path,
            aet = self.aet,
            user = self.user,
            password = self.password
        )

    def put(self, item: Dixel, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Put")

        if item.level is not DicomLevel.INSTANCES:
            raise TypeError("Can only 'put' instances")
        if item.file is None:
            raise ValueError("No file to 'put'")

        r = self.gateway.put(item.file)

    def id_from_item(self, item: Union[Dixel, str],
                     level: DicomLevel=DicomLevel.STUDIES):
        if isinstance(item, Dixel) or hasattr(item, "oid"):
            return item.oid(), item.level
        if isinstance(item, str):
            return item, level
        else:
            raise TypeError("Unable to get id for type {}".format(type(item)))


    def get(self, item: Union[Dixel, str],
            level: DicomLevel=DicomLevel.STUDIES,
            view: OrthancView=OrthancView.TAGS, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Get")

        oid, level = self.id_from_item(item, level)

        try:
            r = self.gateway.get(oid, level, view)
        except GatewayConnectionError as e:
            logger.warning(e)
            r = None

        if r:
            if isinstance(item, Dixel):
                # Want to update with data
                if view==OrthancView.TAGS:
                    item.tags.update(r)
                elif view==OrthancView.FILE:
                    item.file = r
                elif view==OrthancView.META:
                    item.meta.update(r)
                return item
            else:
                # Want a new file
                if view==OrthancView.TAGS:
                    return Dixel(meta={"ID": oid}, tags=r, level=level)
                elif view==OrthancView.FILE:
                    d = Dixel(meta={"ID": oid}, level=level)
                    d.file = r
                    return d
                elif view==OrthancView.META:
                    return Dixel(meta=r, level=level)

        raise FileNotFoundError("Item {} does not exist".format(item))

    def find(self, query: Mapping, level=DicomLevel.STUDIES, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Find")

        q = {"Level": "{!s}".format(level),
             "Query": query }
        r = self.gateway.find(q)

        # Returns a list of OIDs
        return r

    def rfind(self,
              query: Mapping,
              domain: str,
              level=DicomLevel.STUDIES,
              retrieve=False):
        logger = logging.getLogger(self.name)
        logger.debug("Remote Find")

        q = {"Level": "{!s}".format(level),
             "Query": query }

        try:
            r = self.gateway.rfind(q, domain, retrieve=retrieve)
        except Exception as e:
            logger.warning(e)
            r = None

        # Returns a list of maps that should be converted into Dixels
        return r

    def delete(self, item: Union[str, Dixel], level=DicomLevel.STUDIES, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Delete")

        logger.debug(item)

        oid, level = self.id_from_item(item, level)
        r = self.gateway.delete(oid, level)


    def anonymize(self, item: Union[str, Dixel],
                  level=DicomLevel.STUDIES,
                  replacement_map: Mapping=None,
                  **kwargs):

        oid, level = self.id_from_item(item, level)
        if not replacement_map:
            if isinstance(item, Dixel):
                # Must have pre-assigned sham values
                replacement_map = sham_map(item)
            else:
                raise ValueError("Anonymization requires a replacement map or dixel shams")

        return self.gateway.anonymize(oid, level, replacement_map)


    def check(self):
        logger = logging.getLogger(self.name)
        logger.debug("Check")

        try:
            return self.gateway.statistics() is not None
        except GatewayConnectionError as e:
            logger.warning("Failed to connect to Endpoint")
            logger.error(type(e))
            logger.error(e)
            return False


    def patients(self):
        return self.gateway.inventory(level=DicomLevel.PATIENTS)


    def studies(self):
        return self.gateway.inventory(level=DicomLevel.STUDIES)


    def series(self):
        return self.gateway.inventory(level=DicomLevel.SERIES)


    def instances(self):
        return self.gateway.inventory(level=DicomLevel.INSTANCES)


Serializable.Factory.register(Orthanc)