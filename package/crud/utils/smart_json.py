import json
from datetime import timedelta
from pathlib import PosixPath


# Add any serializing functions here
def stringify(obj):

    # Handle bytes from pydicom
    if isinstance(obj, bytes):
        return obj.decode("utf8", "ignore")

    if isinstance(obj, str):
        return obj

    if isinstance(obj, PosixPath):
        return str(obj)

    # Handle DateTime objects
    if hasattr(obj, "isoformat"):
        return obj.isoformat()

    if isinstance(obj, timedelta):
        return obj.__str__()

    # Handle hashes
    if hasattr(obj, 'hexdigest'):
        return obj.hexdigest()


import logging

class SmartJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        out = stringify(obj)
        if out:
            return out
        return json.JSONEncoder.default(self, obj)
