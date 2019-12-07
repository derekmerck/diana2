from enum import IntEnum


class DicomLevel(IntEnum):
    """Enumeration of DICOM levels, ordered by general < specific"""

    PATIENTS = 1
    STUDIES = 2
    SERIES = 3
    INSTANCES = 4

    @staticmethod
    def from_label(label: str):
        if isinstance(label, DicomLevel):
            return label
        if isinstance(label, int):
            return DicomLevel(label)
        if isinstance(label, str):
            return DicomLevel.__dict__[label.upper()]
        raise TypeError

    def __str__(self):
        return self.name.lower()
