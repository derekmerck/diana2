import attr
from .utils import Serializable

@attr.s
class Dixel(Serializable):

    meta = attr.ib(factory=dict)
    file = attr.ib(default=None, repr=False)

    # orthanc id
    def oid(self):
        return self.meta.get('ID')

    # serializer id
    def sid(self):
        return self.meta.get('AccessionNumber')

    # filename
    def fn(self):
        return self.meta.get('FileName')

    def level(self):
        return self.meta.get('level')



