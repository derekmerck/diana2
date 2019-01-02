from enum import Flag, auto

class DixelView(Flag):
    """
    Some endpoints can only generate certain DixelViews, others can
    return Dixel instances with data from multiple views.

    Use `DixelView.TAGS in view` to test for different flags.
    """
    META = auto()   #: In Orthanc this is the data from  /<level>/<oid>
    TAGS = auto()   #: In Orthanc, this is the data from /<level>/<oid>/tags
    FILE = auto()   #: In Orthanc, this is the data from /<level>/<oid>/file
    PIXELS = auto() #: Optional for pydicom readers

    def __str__(self):
        return self.name.lower()