import logging
from io import BytesIO
import numpy as np
from diana.dixel import DixelHashes


def test_hashing():
    h = DixelHashes()
    tags = ["abc", "123", "xyz"]
    data = np.zeros(10)
    _file = BytesIO(b"12345678")

    h.set_meta_hash(tags)
    h.set_data_hash(data)
    h.set_file_hash(_file)

    assert(h.meta_hash.startswith("d"))
    assert(h.file_hash.startswith("7"))
    assert(h.data_hash.startswith("2"))

    h.data_hash = None
    h.evolve_data_hash("012abc")
    assert(h.data_hash != "0")
    h.evolve_data_hash("012abc")
    assert(h.data_hash == "0")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_hashing()