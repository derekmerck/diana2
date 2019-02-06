from pathlib import Path
import yaml, os, logging
from datetime import datetime, timedelta
from diana.apis import Montage, ProxiedDicom
from diana.daemons.collector2 import Collector
from diana.utils.gateways import MontageModality as Modality

# CONFIG
services_path = "/services.yml"
pacs_svc = "pacs"
dest_path = Path("/data/")
montage_svc = "montage"
query = {"q": "", "modality": Modality.CR}
start = datetime(year=2017, month=1, day=1)
stop = datetime(year=2017, month=1, day=5)
# Montage can only query by day
step = timedelta(days=1)
get_meta = False
pool_size = 0


def collect_corpus(_worklist, _pacs, _dest_path):

    c = Collector(pool_size=pool_size)
    c.run(worklist=_worklist,
          source=_pacs,
          dest_path=_dest_path,
          inline_reports=False,
          save_as_im=True,
          anonymize=True)


if __name__ == "__main__":

    logging.basicConfig(level=logging.WARNING)

    with open(services_path) as f:
        services_exp = os.path.expandvars(f.read())
        services = yaml.safe_load(services_exp)

    montage = Montage(**services[montage_svc])
    montage.check()
    worklist = montage.iter_query_by_date(query, start, stop, step, get_meta)

    pacs = ProxiedDicom(**services[pacs_svc])
    pacs.check()

    collect_corpus(worklist, pacs, dest_path)
