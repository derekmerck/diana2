"""
Occasionally something slips through the cracks and
a dataset that should be anonymized ends up containing
inappropriate series like scanned dose reports with PHI.

This script filters a set of zipped studies and removes
unwanted items.

Folder structure is destroyed since filtering is done at
the Dixel-set level, not the file-set data level.

"""

import os, logging
from pprint import pformat
from diana.apis import DcmDir

logging.basicConfig(level=logging.DEBUG)

location = "/Users/derek/Desktop"

ep = DcmDir(path=location)

files = ["test.dum-1.zip"]

# for f in ep.files():
for fi in files:

    contents = ep.get_zipped(fi)

    # for item in contents:
    #     logging.debug("{}: {}: {}".format(item.fn, item.tags.get("Modality"), item.tags.get("SeriesNumber")))

    # contents = list(filter(lambda x: int(x.tags.get("SeriesNumber")) < 9999, contents))
    contents = list(filter(lambda x: x.tags.get("Modality") == "CT", contents))

    # logging.debug(pformat(contents))

    # for item in contents:
    #     logging.debug("{}: {}: {}".format(item.fn, item.tags.get("Modality"), item.tags.get("SeriesNumber")))

    # ep.delete(f)
    fo = "filtered-{}.zip".format('.'.join(os.path.splitext(fi)[:-1]))
    ep.put_zipped(fo, contents)




