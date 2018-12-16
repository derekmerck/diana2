from enum import Flag, auto

class DixelView(Flag):
    META = auto()
    TAGS = auto()
    FILE = auto()
    PIXELS = auto()

    def __str__(self):
        return self.name.lower()