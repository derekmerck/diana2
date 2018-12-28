from typing import Mapping
import attr
from ..utils.dicom import DicomLevel
from ..utils import Endpoint, Serializable
from . import Orthanc

@attr.s
class ProxiedDicom(Endpoint, Serializable):

    name = attr.ib( default="ProxiedDicom" )
    proxy_desc = attr.ib( factory=dict )
    proxy_domain = attr.ib( type=str, default="remote" )

    proxy = attr.ib( init=False )
    @proxy.default
    def setup_proxy(self):
        if self.proxy_desc.get("ctype"):
            self.proxy_desc.pop("ctype")
        return Orthanc(**self.proxy_desc)

    def find(self, query: Mapping, level=DicomLevel.STUDIES, retrieve: bool=False, **kwargs):
        return self.proxy.rfind(query=query,
                                level=level,
                                domain=self.proxy_domain,
                                retrieve=retrieve)
