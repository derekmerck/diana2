from enum import Enum, auto

class DicomEventType(Enum):
    INSTANCE_ADDED = auto()
    SERIES_ADDED = auto()
    STUDY_ADDED = auto()
    PATIENT_ADDED = auto()
    FILE_ADDED = auto()