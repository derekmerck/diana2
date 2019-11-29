
import re

_SAFE_PATH_RE = re.compile(r'[^a-zA-Z0-9\-\_\=\.]')
_MAX_PATH_NAME_LEN = 255


def path_safe(in_str):
    norm_str = _SAFE_PATH_RE.sub(
        '_', in_str.strip())
    if len(norm_str.strip('.')) == 0:
        # making sure the normalized result is non-empty, and not just dots
        raise ValueError(in_str)
    return norm_str[:_MAX_PATH_NAME_LEN]
