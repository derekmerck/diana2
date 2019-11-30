import logging
from typing import Mapping, Union
# from pprint import pformat
import attr
from ..dixel import Dixel, ShamDixel, DixelView
from crud.abc import Endpoint, Serializable
# from ..utils import Endpoint, Serializable
from ..utils.gateways import Orthanc as OrthancGateway, GatewayConnectionError
from ..utils.dicom import DicomLevel

# Special metadata:
# $ export ORTHANC_METADATA_0=Source,9876

#
# def sham_map(d: ShamDixel):
#
#     if d.level > DicomLevel.STUDIES:
#         raise NotImplementedError("Can only create default sham maps for STUDIES")
#
#     logging.debug(d)
#
#     m = {
#         "Replace": {
#             "PatientName": d.meta["ShamName"],
#             "PatientID": d.meta["ShamID"],
#             "PatientBirthDate": d.meta["ShamBirthDate"],
#             "AccessionNumber": d.meta["ShamAccessionNumber"],
#             "StudyDate": d.ShamStudyDate(),
#             "StudyTime": d.ShamStudyTime(),
#             },
#         "Keep": [
#             "PatientSex",
#             'StudyDescription',
#             'SeriesDescription',
#             ],
#         "Force": True
#     }
#     return m


@attr.s
class Orthanc(Endpoint, Serializable):

    name = attr.ib(default="Orthanc")

    protocol = attr.ib(default="http")
    host = attr.ib(default="localhost")
    port = attr.ib(default=8042)
    path = attr.ib(default=None)
    aet = attr.ib(default="ORTHANC")
    peername = attr.ib(default="orthanc")

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

    # Valid keys for metadata kv store
    meta_keys = attr.ib(default=list)

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

    def psend(self, item: Union[Dixel, str], dest: Union['Orthanc', str]):
        logger = logging.getLogger(self.name)
        logger.debug("Get")

        oid, _ = self.id_from_item(item, None)

        if isinstance(dest, Orthanc):
            dest = dest.peername

        self.gateway.send(oid, dest, "peers")

    # TODO: Need a view for orthanc-metadata, ie, AnonymizedFrom

    def get(self, item: Union[str, Dixel],
            level: DicomLevel = DicomLevel.STUDIES,
            view: DixelView = DixelView.TAGS, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Get")

        oid, level = self.id_from_item(item, level)

        try:
            r = self.gateway.get(oid, level, str(view))
        except GatewayConnectionError as e:
            # e = "Gateway connection error"
            logger.warning(e)
            r = None

        if r:
            logging.debug(isinstance(item, Dixel))
            if isinstance(item, Dixel):
                # Want to update with data
                if DixelView.TAGS in view:
                    item.tags.update(r)
                    item.simplify_tags()
                elif DixelView.FILE in view:
                    item.file = r
                elif DixelView.META in view:
                    item.meta.update(r)
                elif DixelView.METAKV in view:
                    item.meta.update(r)
                return item
            else:
                # Want a new file
                if DixelView.TAGS in view:
                    d = Dixel.from_orthanc(meta={"ID": oid},
                                           tags=r,
                                           level=level)

                elif DixelView.FILE in view:
                    d = Dixel(meta={"ID": oid}, level=level)
                    d.file = r

                elif DixelView.META in view:
                    d = Dixel(meta=r, level=level)

                return d

        raise FileNotFoundError("Item {} does not exist".format(oid))

    def getm(self, item: Union[str, Dixel],
             level: DicomLevel = DicomLevel.STUDIES,
             key: str = "meta"):

        logger = logging.getLogger(self.name)
        logger.debug("Get Meta")

        oid, level = self.id_from_item(item, level)

        try:
            r = self.gateway.get_metadata(oid, level, key)
        except GatewayConnectionError as e:
            # e = "Gateway connection error"
            logger.warning(e)
            r = None

        return r

    def putm(self, item: Union[str, Dixel],
             level: DicomLevel = DicomLevel.STUDIES,
             key: str = "meta",
             value: str = "",
             **kwargs):

        logger = logging.getLogger(self.name)
        logger.debug("Put Meta")

        oid, level = self.id_from_item(item, level)

        try:
            r = self.gateway.put_metadata(oid, level, key, value)
        except GatewayConnectionError as e:
            # e = "Gateway connection error"
            logger.warning(e)
            r = None

        return r

    def find(self, item: Union[Mapping, Dixel],
             level=DicomLevel.STUDIES, **kwargs) -> list:
        logger = logging.getLogger(self.name)
        logger.debug("Find")

        if isinstance(item, Dixel):
            query = item.query()
            level = item.level
        else:
            query = item

        q = {"Level": "{!s}".format(level),
             "Query": query }

        # logger.debug(pformat(q))

        results = self.gateway.find(q)

        # Returns a list of OIDs that must be converted to dixels

        if results:
            rv = []
            for oid in results:
                item = Dixel(meta={"ID": oid}, level=level)
                rv.append(item)
            return rv

    def rfind(self,
              item: Union[Mapping, Dixel],
              domain: str,
              level=DicomLevel.STUDIES,
              retrieve=False) -> list:
        logger = logging.getLogger(self.name)
        logger.debug("Remote Find")

        if isinstance(item, Dixel):
            query = item.query()
            level = item.level
        else:
            query = item

        q = {"Level": "{!s}".format(level),
             "Query": query }

        # logger.debug(pformat(q))
        # logger.debug(retrieve)

        try:
            r = self.gateway.rfind(q, domain, retrieve=retrieve)
        except GatewayConnectionError as e:
            # e = "Gateway connection error"
            logger.warning(e)
            r = None

        # Returns a list of maps that should be converted into Dixels
        return r

    def delete(self, item: Union[str, Dixel], level=DicomLevel.STUDIES, **kwargs):
        logger = logging.getLogger(self.name)
        logger.debug("Delete")

        oid, level = self.id_from_item(item, level)
        r = self.gateway.delete(oid, level)

    def clear(self):
        for item in self.patients():
            self.gateway.delete(item, DicomLevel.PATIENTS)

    def modify(self, item: Union[str, Dixel],
                  level=DicomLevel.STUDIES,
                  replacement_map: Mapping = None,
                  **kwargs):

        oid, level = self.id_from_item(item, level)
        if not replacement_map:
            raise ValueError("Modification requires explicit replacement map")

        return self.gateway.modify(oid, level, replacement_map)

    def anonymize(self, item: Union[str, Dixel],
                  level=DicomLevel.STUDIES,
                  replacement_map: Mapping = None,
                  use_default_map: bool = False,
                  **kwargs):

        oid, level = self.id_from_item(item, level)
        if not replacement_map:
            if use_default_map:
                sham_dixel = ShamDixel.from_dixel(item)
                replacement_map = sham_dixel.orthanc_sham_map()
            else:
                raise ValueError("Anonymization requires a replacement map or "
                                 "explicit \"use_default_map\" flag")

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

    def info(self):
        logger = logging.getLogger(self.name)
        logger.debug("Info")

        try:
            return self.gateway.statistics()
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


Orthanc.register()
