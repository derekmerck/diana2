import json
import logging
from datetime import timedelta
from pathlib import PosixPath

logger = logging.getLogger("SmartJSONEnc")
logger.setLevel(level=logging.ERROR)

# Add any serializing functions here
def stringify(obj):
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

    # Handle bytes from pydicom
    if isinstance(obj, bytes):
        return obj.decode("utf8", "ignore")


class SmartJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        out = stringify(obj)
        if out:
            return out

        try:
            return json.JSONEncoder.default(self, obj)
        except TypeError as e:
            logger = logging.getLogger("SmartJSONEnc")
            logger.warning(e)
            logger.warning("Failed to encode {}; skipping".format(obj))




