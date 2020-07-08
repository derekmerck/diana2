import hashlib
import typing as typ
import attr
import numpy as np
from crud.abc import Serializable

_hash = hashlib.sha224


@attr.s(auto_attribs=True)
class DixelHashes(Serializable):
    meta_hash: str = None
    file_hash: str = None
    data_hash: str = None

    def set_meta_hash(self, tags: typ.List[str]):
        _tags = "|".join(tags).encode("utf8")
        self.meta_hash = _hash(_tags).hexdigest()

    def set_file_hash(self, _file: typ.BinaryIO):
        self.file_hash = _hash(_file.read()).hexdigest()

    def set_data_hash(self, data: np.ndarray):
        _data = bytes(data)
        self.data_hash = _hash(_data).hexdigest()

    def evolve_data_hash(self, data: str):
        if self.data_hash is None:
            # Initialize an evolving hash
            self.data_hash = data
        else:
            current_val = int(self.data_hash, 16)
            input_val = int(data, 16)
            new_val = current_val ^ input_val
            self.data_hash = f'{new_val:x}'
