from enum import Enum, auto

class DicomEvent(Enum):
    INSTANCE_ADDED = auto()
    SERIES_ADDED = auto()
    STUDY_ADDED = auto()
    PATIENT_ADDED = auto()
