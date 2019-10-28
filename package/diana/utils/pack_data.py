from cryptography.fernet import Fernet
import json
import logging
from typing import Mapping, Union

from . import SmartJSONEncoder


def pack_data(data: Mapping, fkey: Union[str, bytes], fields=None):
    logging.debug(f"Packing fields: {fields}")
    if isinstance(fkey, str):
        fkey = fkey.encode("utf8")
    if fields:
        data = {k: v for k, v in data.items() if k in fields}
    clear = json.dumps(data, cls=SmartJSONEncoder).encode("utf8")
    rv = Fernet(fkey).encrypt(clear)
    return rv


def unpack_data(data: Union[str, bytes], fkey: Union[str, bytes]):
    if isinstance(data, str):
        data = data.encode("utf8")
    if isinstance(fkey, str):
        fkey = fkey.encode("utf8")
    clear = Fernet(fkey).decrypt(data)
    rv = json.loads(clear)
    return rv
