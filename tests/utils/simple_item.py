import attr
from datetime import datetime
from crud.abc import Serializable

@attr.s
class SimpleItem(Serializable):

    data = attr.ib(default=None)
    meta = attr.ib(factory=dict)

    def __attrs_post_init__(self):
        self.meta['creation_time'] = datetime.now()
        if self.meta.get('epid'):
            self.epid = self.meta['epid']
        else:
            self.meta['epid'] = self.epid


# Have to register anything that will be flattened
SimpleItem.register()
