"""
Merck
Fall 2018

Generate an NLTK format text corpus from reports using Montage.

1. For each chunk interval (2wks)
2.   For each interval in that chunk (1day)
3.     Find all reports in Montage (Requires repeated requests)
4.     For each report:
5.       Save meta data
6.       Anonymize
7.       Save as nltk corpus file
8.   Create a chunk index file

Examples:

docker run -it -v "/home/derek/.secrets/lifespan_services.yml:/services.yml" -v "/home/derek/data/radcat_1y:/data" derekmerck/diana2 /bin/bash

- 2017/11/1 - 2018/12/31: ~500k entries (RADCAT)

docker run -it -v "/home/derek/.secrets/lifespan_services.yml:/services.yml" -v "/home/derek/data/cr_all:/data" derekmerck/diana2 /bin/bash

- 2014/1/1 - 2018/12/31: ~1.1M entries (no XR, "modern" report template)


"""

import logging, csv, os
from hashlib import md5
from pathlib import Path
import yaml
from datetime import datetime, timedelta
from diana.apis import Montage
from diana.utils.gateways import TextFileHandler, MontageModality as Modality, supress_urllib_debug

# --------------------------
# Project Config
# --------------------------

data_path = Path("/data")
services_path = "/services.yml"
montage_svc = "montage"
start_date = datetime(year=2014, month=1, day=1).date()
end_date = datetime(year=2018, month=12, day=31).date()
chunk_interval = {"weeks": 2}
query_interval = {"days": 1}
key_fn_fmt = "corpus_meta.{}-{}.csv"

# Any study
# q = {"q": ""}

# Any XR or CR study
q = {"q": "",
     "modality": [Modality.XR,
                  Modality.CR]
    }

# --------------------------
# Initialization
# --------------------------

logging.basicConfig(level=logging.DEBUG)
supress_urllib_debug()

with open(services_path) as f:
    services = yaml.load(f)

M = Montage(**services[montage_svc])
M.check()

F = TextFileHandler(path=data_path/"corpus", subpath_depth=2, subpath_width=2)

# --------------------------
# Helpers
# --------------------------

def daterange(start, end, step=timedelta(days=1)):
    curr = start
    while (curr < end) if (end > start) else (curr > end):
        yield curr, min(curr+step, end)
        curr += step

def get_daily_events(start, end):
    query = {**q,
         "start_date": start.isoformat(),
         "end_date": end.isoformat()}
    data = M.find(query)

    result = []
    for d in data:

        try:
            radcat = d.report.radcat()
        except ValueError:
            radcat = ''

        item_meta = {
            "id": md5(d.tags["AccessionNumber"].encode("UTF-8")).hexdigest(),
            "modality": d.tags["Modality"],
            "body_part": d.meta['BodyParts'],
            "cpts": d.meta['CPTCodes'],
            "status": d.meta['PatientStatus'],
            "age": d.meta["PatientAge"],
            "sex": d.tags["PatientSex"],
            "radcat": radcat
        }

        logging.debug(item_meta)
        # logging.debug(d.report)
        # logging.debug(d.report.anonymized())

        fn = "{}.txt".format(item_meta['id'])
        F.put(fn, d.report.anonymized())

        result.append(item_meta)

    return result

# --------------------------
# Processing Loop
# --------------------------

chunks = daterange(start_date, end_date, step=timedelta(**chunk_interval))
for startc, endc in chunks:
    chunk_data = []
    daily = daterange(startc, endc, step=timedelta(**query_interval))

    for startd, endd in daily:
        result = get_daily_events(startd, endd)
        chunk_data += result

    csv_fn = key_fn_fmt.format(startc.strftime("%y%m%d"), endc.strftime("%y%m%d"))
    logging.debug(csv_fn)

    os.makedirs( data_path / "meta", exist_ok=True )
    csv_fp = data_path / "meta" / csv_fn
    with open(csv_fp, "w") as f:
        C = csv.DictWriter(f, fieldnames=
                ["id", "modality", "body_part", "cpts",
                 "status", "age", "sex", "radcat"] )
        C.writeheader()
        C.writerows(chunk_data)
