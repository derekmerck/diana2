from typing import Mapping
import attr
from ..utils.dicom import DicomLevel
from ..utils import Endpoint, Serializable
from . import Orthanc


class ProxiedDicom(Endpoint, Serializable):

    name = attr.ib( default="ProxiedDicom" )
    proxy_desc = attr.ib( type=dict )
    gateway = attr.ib( init=False )

    @gateway.default
    def setup_gateway(self):
        return Orthanc(**self.proxy_desc)

    def find(self, query: Mapping, level=DicomLevel.STUDIES, retrieve: bool=False, **kwargs):
        return self.gateway.rfind(query, level, self.name, retrieve=retrieve)
