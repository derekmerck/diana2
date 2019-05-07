
# read the key
# read the file list

# for each unfiltered zip file
#   determine the source study date
#   if study date is after 6/8/18
#     check if sham a/n in filtered-*
#     open and filter it
#     if any changes
#       save the file

# count number of studies to evaluate
# count number of studies already processed
# count number of studies newly processed

import os, logging, re, datetime
from dateutil import parser as DateTimeParser
from diana.apis import CsvFile, DcmDir

location = "/Users/derek/Desktop"
key = "rimiprostate.key.csv"
files = "rimiprostate.files.txt"
target_dt = datetime.datetime(year=2018, month=6, day=8, hour=0, minute=0, second=0)

logging.basicConfig(level=logging.DEBUG)

c = CsvFile(fp=os.path.join(location, key))
c.read()

sans_after_target = []
for item in c.dixels:
    study_dt = DateTimeParser.parse(item.meta['StudyDateTime'])
    if study_dt > target_dt:
        an = item.meta['ShamAccessionNumber'][0:16]
        # logging.debug(an)
        sans_after_target.append(an)

logging.info("Num studies: {}".format(len(c.dixels)))
logging.info("Num studies after target: {}".format(len(sans_after_target)))

ll = []
with open(os.path.join(location,files)) as f:
    l = f.readlines()
    for item in l:
        ll.append(item.rstrip())

r = re.compile(r'^(?!filtered-).*')

files_available = filter(lambda x: r.match(x), ll)
sans_available = []
for item in files_available:
    an = os.path.splitext(item)[0]
    # logging.debug(an)
    sans_available.append(an)

logging.info("Num files available: {}".format(len(sans_available)))

candidate_sans = []
for item in sans_available:
    if item in sans_after_target:
        candidate_sans.append(item)

logging.info("Num files after target: {}".format(len(candidate_sans)))

completed_fs = filter(lambda x: not r.match(x), ll)
completed_sans = []
for item in completed_fs:
    an = os.path.splitext(item)[0][-16:]
    # logging.debug(an)
    completed_sans.append(an)

logging.info("Num files already filtered: {}".format(len(completed_sans)))

files_to_handle = []
for item in candidate_sans:
    if item not in completed_sans:
        files_to_handle.append(item)

logging.info("Num files remaining to be filtered: {}".format(len(files_to_handle)))

unnecessary_filters = []
for item in completed_sans:
    if item not in candidate_sans:
        unnecessary_filters.append(item)

logging.info("Num files unncessarily(?) filtered: {}".format(len(unnecessary_filters)))


ep = DcmDir(path=location)

for item in files_to_handle:

    fi = "{}.zip".format(item)

    try:
        contents = ep.get_zipped(fi)
    except:
        continue

    # for item in contents:
    #     logging.debug("{}: {}: {}".format(item.fn, item.tags.get("Modality"), item.tags.get("SeriesNumber")))

    contents = list(filter(lambda x: int(x.tags.get("SeriesNumber"), 0) < 9999, contents))
    # contents = list(filter(lambda x: x.tags.get("Modality") == "CT", contents))

    # logging.debug(pformat(contents))

    # for item in contents:
    #     logging.debug("{}: {}: {}".format(item.fn, item.tags.get("Modality"), item.tags.get("SeriesNumber")))

    # ep.delete(f)
    fo = "filtered-{}.zip".format('.'.join(os.path.splitext(fi)[:-1]))
    ep.put_zipped(fo, contents)







