from .requester import Requester
from ..dicom import DicomLevel
import attr

from enum import Enum

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

    def find(self, query):
        resource = "tools/find"
        return self._post(resource, json=query)

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
            resource = "{!s}/{}/file".format(level, oid)
        else:
            raise TypeError("Unknown view requested")

        return self._get(resource)

    def statistics(self):
        return self._get("statistics")