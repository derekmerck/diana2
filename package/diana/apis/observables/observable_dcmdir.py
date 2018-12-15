from diana.apis import DcmDir
from diana.utils.endpoint import Event, ObservableMixin

class ObservableDcmDir(DcmDir, ObservableMixin):

    def changes(self, **kwargs):
        raise NotImplementedError

