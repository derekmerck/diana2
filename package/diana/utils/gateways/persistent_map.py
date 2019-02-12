import pickle, logging, csv, hashlib, os, glob
from multiprocessing import Queue
import attr
from abc import ABC
import time


def md5_digest(value):
    return hashlib.md5(value.encode("utf8")).hexdigest()


@attr.s
class PersistentMap(ABC):

    keyhash_func = attr.ib( default=md5_digest )
    fn = attr.ib( type=str, default=None )
    observed_keys = attr.ib( init=False, factory=set)

    def clear(self):
        if os.path.isfile(self.fn):
            os.remove(self.fn)

    def put(self, key, item, early_exit=True):

        if self.keyhash_func:
            key = self.keyhash_func(key)
        logging.debug("Adding to pmap")

        if early_exit and (key in self.observed_keys):
            logging.debug("Item already exists in pmap (from observed), skipping")
            return

        data = self.read_data(key)
        if early_exit:
            for _key in data.keys():
                self.observed_keys.add(_key)

        if early_exit and (key in data.keys()):
            logging.debug("Item already exists in pmap (read file), skipping")
            return

        logging.debug("Adding item to key")
        data[key] = item
        self.write_data(data, key)

    def get(self, key):
        if self.keyhash_func:
            key = self.keyhash_func(key)
        logging.debug("Retrieving from pmap")
        data = self.read_data(key)
        return data.get(key)

    def read_data(self, key):
        raise NotImplemented

    def write_data(self, data, key):
        raise NotImplemented

    def run(self, queue, early_exit=True):
        while True:
            logging.debug("Checking queue: {}".format(
                "Empty" if queue.empty() else "Pending"))
            if not queue.empty():
                key, item = queue.get(False)
                logging.debug("Found ({}, {})".format(key, item))
                self.put(key, item, early_exit=early_exit)
            time.sleep(0.2)


@attr.s
class PicklePMap(PersistentMap):

    fn = attr.ib( type=str, default="/tmp/cache.pkl" )

    def read_data(self, *args, **kwargs):
        if not os.path.isfile(self.fn):
            return {}
        with open(self.fn, "rb") as f:
            data = pickle.load(f)
        logging.debug("READING PKL: {}".format(data))
        return data

    def write_data(self, data, *args, **kwargs):
        with open(self.fn, "wb") as f:
            pickle.dump(data, f)
        logging.debug("WRITING PKL: {}".format(data))


@attr.s
class CSVPMap(PersistentMap):

    fn = attr.ib( type=str, default="/tmp/cache.csv" )
    keyfield = attr.ib( default="_key" )
    fieldnames = attr.ib( default=None )

    def read_data(self, *args, **kwargs):
        if not os.path.isfile(self.fn):
            return {}
        with open(self.fn, "r") as f:
            data = {}
            reader = csv.DictReader(f)
            for row in reader:
                _key = row.pop(self.keyfield)
                data[_key] = {**row}
            logging.debug("READING CSV: {}".format(data))
            return data

    def write_data(self, data, *args, **kwargs):
        rows = []
        for k,v in data.items():
            _row = v
            _row[self.keyfield] = k
            rows.append(_row)

        if self.fieldnames:
            fieldnames = self.fieldnames
        else:
            _fieldnames = set()
            for item in rows:
                for k in item.keys():
                    _fieldnames.add(k)
            fieldnames = list(_fieldnames)

        with open(self.fn, "w") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        logging.debug("WRITING CSV: {}".format(data))


@attr.s
class ArrayPMapMixin(PersistentMap):

    prefix_len = attr.ib(default=2)  # 16*16 = 256 files for a hexdigest
    backends = attr.ib(init=False, factory=dict)

    def clear(self):
        for be in self.backends.values():
            be.clear()

    def mk_backend(self) -> PersistentMap:
        raise NotImplementedError

    def backend_for(self, key):
        be_key = key[0:self.prefix_len]
        be = self.backends.get(be_key)
        if not be:
            if self.fn:
                fn = self.fn.format(be_key)
            else:
                fn = None
            if isinstance(self, PicklePMap):
                be = PicklePMap(fn=fn)
            elif isinstance(self, CSVPMap):
                be = CSVPMap(fn=fn, keyfield=self.keyfield, fieldnames=self.fieldnames)
            self.backends[be_key] = be
        return be

    def read_data(self, key, *args, **kwargs):
        be = self.backend_for(key)
        data = be.read_data()
        return data

    def write_data(self, data, key, *args, **kwargs):
        be = self.backend_for(key)
        be.write_data(data)


@attr.s
class PickleArrayPMap(ArrayPMapMixin, PicklePMap):
    fn = attr.ib( type=str, default="/tmp/cache-{}.pkl" )


@attr.s
class CSVArrayPMap(ArrayPMapMixin, CSVPMap):
    fn = attr.ib( type=str, default="/tmp/cache-{}.csv" )

