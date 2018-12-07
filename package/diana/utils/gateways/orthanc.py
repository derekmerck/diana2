from hashlib import sha1
from enum import Enum
import attr
from .requester import Requester
from ..dicom import DicomLevel


def orthanc_hash(PatientID: str, StudyInstanceUID: str, SeriesInstanceUID=None, SOPInstanceUID=None) -> sha1:
    if not SeriesInstanceUID:
        s = "|".join([PatientID, StudyInstanceUID])
    elif not SOPInstanceUID:
        s = "|".join([PatientID, StudyInstanceUID, SeriesInstanceUID])
    else:
        s = "|".join([PatientID, StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID])
    return sha1(s.encode("UTF8"))


def orthanc_id(PatientID: str, StudyInstanceUID: str, SeriesInstanceUID=None, SOPInstanceUID=None) -> str:
    h = orthanc_hash(PatientID, StudyInstanceUID, SeriesInstanceUID, SOPInstanceUID)
    d = h.hexdigest()
    return '-'.join(d[i:i+8] for i in range(0, len(d), 8))


class OrthancView(Enum):
    TAGS = "tags"
    INFO = "info"
    FILE = "file"


@attr.s
class Orthanc(Requester):

    name = attr.ib(default="Orthanc")
    port = attr.ib(default=8042)
    user = attr.ib(default="orthanc")
    password = attr.ib(default="passw0rd!")
    aet = attr.ib(default="ORTHANC")

    def find(self, query):
        resource = "tools/find"
        return self._post(resource, json=query)

    def rfind(self, query, domain, retrieve=False):
        # logger = logging.getLogger(name=self.name)

        result = []

        resource = "modalities/{}/query".format(domain)
        response0 = self._post(resource, json=query)
        # logger.debug(response0)

        if response0.get('ID'):
            resource = "queries/{}/answers".format(response0.get('ID'))
            response1 = self._get(resource)
            # logger.debug(response1)

            for answer in response1:
                # logger.debug(answer)
                resource = "queries/{}/answers/{}/content?simplify".format(response0.get('ID'), answer)
                response2 = self._get(resource)
                result.append(response2)

                if retrieve:
                    resource = "queries/{}/answers/{}/retrieve".format(response0.get('ID'), answer)
                    response3 = self._post(resource, data=self.aet)

                # logger.debug(response2)

        return result


    def put(self, file):
        resource = "instances"
        return self._post(resource, data=file)

    def get(self, oid: str, level: DicomLevel, view: OrthancView=OrthancView.TAGS):

        if view == OrthancView.TAGS:
            if level == DicomLevel.INSTANCES:
                resource = "{!s}/{}/tags?simplify".format(level, oid)
            else:
                resource = "{!s}/{}/shared-tags?simplify".format(level, oid)
        elif view == OrthancView.INFO:
            resource = "{!s}/{}".format(level, oid)
        elif view == OrthancView.FILE:
            if level == DicomLevel.INSTANCES:
                resource = "{!s}/{}/file".format(level, oid)
            else:
                resource = "{!s}/{}/archive".format(level, oid)
        else:
            raise TypeError("Unknown view requested")

        return self._get(resource)

    def delete(self, oid, level):
        resource = "{!s}/{}".format(level, oid)
        return self._delete(resource)

    def anonymize(self, oid, level, replacement_map):
        resource = "{!s}/{}/anonymize".format(level, oid)
        response = self._post(resource, json=replacement_map)
        return response.get("ID")

    def inventory(self, level = DicomLevel.STUDIES):
        resource = "{!r}".format(level)
        return self._get(resource)

    def statistics(self):
        return self._get("statistics")

    def reset(self):
        return self._post("tools/reset")

    def changes(self, current=0, limit=10):
        params = { 'since': current, 'limit': limit }
        return self._get("changes", params=params)