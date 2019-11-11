from typing import Union, Mapping, List
from os import PathLike
import os
import io
import yaml
import logging


def deserialize_str(value: Union[str, io.IOBase, PathLike] ) -> str:
    """Convert read @file.txt to str or return input str"""

    if not value:
        return ""

    logging.debug(f"Deserializing str: {value}")

    # Try to import a file
    if isinstance(value, io.StringIO) or isinstance(value, io.FileIO):
        f = value
        s = f.read()
    elif isinstance(value, PathLike):
        with open(str(value)) as f:
            s = f.read()
    elif isinstance(value, str) and value.startswith("@"):
        with open(value[1:]) as f:
            s = f.read()
    else:
        # It's a string input
        s = value

    return s



def deserialize_array(value: Union[str, io.IOBase, PathLike] ) -> List:
    """Convert comma or line delimited str or @file.txt to array"""

    if not value:
        return []

    logging.debug(f"Deserializing array: {value}")

    # Try to import a file
    if isinstance(value, io.StringIO) or isinstance(value, io.FileIO):
        f = value
        s = f.readlines()
    elif isinstance(value, PathLike):
        with open(str(value)) as f:
            s = f.readlines()
    elif isinstance(value, str) and value.startswith("@"):
        with open(value[1:]) as f:
            s = f.readlines()
    else:
        # It's a string/json input
        s = value.split(",")

    return s


def deserialize_dict(value: Union[str, io.IOBase, PathLike] ) -> Mapping:
    """Convert json str or @file.yaml to dict"""

    if not value:
        return {}

    logging.debug(f"Deserializing dict: {value}")

    # Try to import a file
    if isinstance(value, io.StringIO) or isinstance(value, io.FileIO):
        f = value
        s = f.read()
    elif isinstance(value, PathLike):
        with open(str(value)) as f:
            s = f.read()
    elif isinstance(value, str) and value.startswith("@"):
        with open(value[1:]) as f:
            s = f.read()
    else:
        # It's a string/json input
        s = value

    _s = os.path.expandvars(s)

    result = list(yaml.safe_load_all(_s))
    if len(result) == 1:
        return result[0]

    return result