from enum import IntEnum

class DicomLevel(IntEnum):
    """Enumeration of DICOM levels, ordered by general < specific"""

    PATIENTS = 1
    STUDIES = 2
    SERIES = 3
    INSTANCES = 4

    def __str__(self):
        return self.name.lower()