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
        self.meta_hash = self.hash_meta(tags)

    def set_file_hash(self, _file: typ.Union[typ.BinaryIO, bytes]):
        self.file_hash = self.hash_file(_file)

    def set_data_hash(self, data: np.ndarray):
        self.data_hash = self.hash_data(data)

    def evolve_data_hash(self, data: str):
        if self.data_hash is None:
            # Initialize an evolving hash
            self.data_hash = data
        else:
            self.data_hash = self.xor_hashes(self.data_hash, data)

    @classmethod
    def hash_meta(cls, tags: typ.List[str]):
        _tags = "|".join(tags).encode("utf8")
        return _hash(_tags).hexdigest()

    @classmethod
    def hash_file(self, _file: typ.Union[typ.BinaryIO, bytes]):
        if hasattr(_file, "read"):
            return _hash(_file.read()).hexdigest()
        else:
            return _hash(_file).hexdigest()

    @classmethod
    def hash_data(self, data: np.ndarray):
        _data = bytes(data)
        return _hash(_data).hexdigest()

    @classmethod
    def xor_hashes(self, h0, h1):
        h0_val = int(h0, 16)
        h1_val = int(h1, 16)
        new_val = h1_val ^ h0_val
        return f'{new_val:x}'
