"""
Occasionally something slips through the cracks and
a dataset that should be anonymized ends up containing
inappropriate series like scanned dose reports with PHI.

This script filters a set of zipped studies and removes
unwanted items.

"""

from diana.apis import DcmDir

location = "/Users/derek/Desktop"

ep = DcmDir(location)

for f in ep.files():

    contents = ep.get_zipped(f)
    filter(lambda x: True if int(x.tags.get("SeriesNumber")) > 900,
           contents)
    item = contents.zip()

    ep.delete(item)
    ep.put_zipped(contents)




