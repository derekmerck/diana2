from enum import Flag, auto

class DixelView(Flag):
    """
    Some endpoints can only generate certain DixelViews, others can
    return Dixel instances with data from multiple views.
    """
    META = auto()  #: In Orthanc this is the data from  /<level>/<oid>
    TAGS = auto()  #: In Orthanc, this is the data from /<level>/<oid>/tags
    FILE = auto()  #: In Orthanc, this is the data from /<level>/<oid>/file
    PIXELS = auto()

    def __str__(self):
        return self.name.lower()