import json
from datetime import timedelta

# Add any serializing functions here
def stringify(obj):
    if isinstance(obj, str):
        return obj

    # Handle DateTime objects
    if hasattr(obj, "isoformat"):
        return obj.isoformat()

    if isinstance(obj, timedelta):
        return obj.__str__()

    # Handle hashes
    if hasattr(obj, 'hexdigest'):
        return obj.hexdigest()



class SmartJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        out = stringify(obj)
        if out:
            return out

        return json.JSONEncoder.default(self, obj)


