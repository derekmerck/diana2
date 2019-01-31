import logging, hashlib
from datetime import datetime
from multiprocessing import Pool, Value
from functools import partial
import attr
from ..apis import Redis, DcmDir, Orthanc
from ..dixel import DixelView
from ..utils.dicom import DicomFormatError

checked = Value('i', 0)
registered = Value('i', 0)
uploaded = Value('i', 0)


def index_file(fn, path=None, reg=None, prefix=None, counter0: Value=checked, counter1: Value=registered):

    counter0.value += 1
    if counter0.value % 1000 == 0:
        print("Indexing - {} checked".format(counter0.value))
    if not isinstance(reg, Redis):
        reg = Redis(**reg)
    try:
        d = DcmDir(path=path).get(fn, view=DixelView.TAGS)
        reg.add_to_collection(d, path=path, prefix=prefix)
        logging.info("Registered DICOM file {}".format(fn))
        counter1.value+=1
    except DicomFormatError:
        logging.debug("Skipping non-DICOM or poorly formatted file {}".format(fn))
        pass
    except FileNotFoundError:
        logging.warning("Skipping improperly requested file")
        pass


def put_inst(fn, dest, counter: Value=uploaded):

    d = DcmDir().get(fn, view=DixelView.FILE)  # Don't need pydicom data
    if not isinstance(dest, Orthanc):
        dest = Orthanc(**dest)
    dest.put(d)
    counter.value+=1
    if counter.value % 1000 == 0:
        print("Uploading - {} handled".format(counter.value))


@attr.s
class FileIndexer(object):
    """Create a registry for all files in a DICOM directory and subdirs"""

    pool_size = attr.ib( default=0 )
    pool = attr.ib( init=False, repr=False )
    @pool.default
    def create_pool(self):
        if self.pool_size > 0:
            return Pool(self.pool_size)

    @staticmethod
    def prefix_for_path(basepath):
        reg_prefix = hashlib.md5(basepath.encode("UTF-*")).hexdigest()[0:4] + "-"
        return reg_prefix

    @staticmethod
    def items_on_path(basepath, registry):
        reg_prefix = FileIndexer.prefix_for_path(basepath)
        count = registry.collections(prefix=reg_prefix)
        return count

    def index_path(self,
                   basepath,
                   registry,
                   rex="*.dcm",
                   recurse_style="UNSTRUCTURED"):

        checked.value = 0
        registered.value = 0
        tic = datetime.now()

        print("Indexing path: {}".format(basepath))

        reg_prefix = FileIndexer.prefix_for_path(basepath)
        D = DcmDir(path=basepath, recurse_style=recurse_style)
        for path in D.subdirs():
            print("Working on path: {}".format(path))
            files = DcmDir(path=path).files(rex=rex)

            if self.pool_size == 0:
                for fn in files:
                    index_file(fn,
                               path=path,
                               reg=registry,
                               prefix=reg_prefix)
            else:
                p = partial(index_file,
                            path=path,
                            reg=registry.asdict(),
                            prefix=reg_prefix )
                self.pool.map(p, files)

        toc = datetime.now()
        elapsed_time = (toc-tic).seconds or 1
        checking_rate =  checked.value / elapsed_time
        handling_rate =  registered.value / elapsed_time

        print("Indexed {} objects of {} checked in {} seconds".format(registered.value, checked.value, elapsed_time))
        print("Checking rate: {} files per second".format(round(checking_rate,1)))
        print("Handling rate: {} files per second".format(round(handling_rate,1)))

    def upload_path(self, basepath, registry: Redis, dest: Orthanc):

        tic = datetime.now()
        uploaded.value = 0

        print("Uploading path: {}".format(basepath))

        reg_prefix = FileIndexer.prefix_for_path(basepath)
        for collection in registry.collections(prefix=reg_prefix):
            self.upload_collection(collection, basepath, registry, dest)

        toc = datetime.now()
        elapsed_time = (toc - tic).seconds or 1
        handling_rate =  uploaded.value / elapsed_time

        print("Uploaded {} objects in {} seconds".format(uploaded.value, elapsed_time))
        print("Handling rate: {} files per second".format(round(handling_rate,1)))

    def upload_collection(self, collection, basepath, registry, dest):
        reg_prefix = FileIndexer.prefix_for_path(basepath)
        files = registry.collected_items(collection, prefix=reg_prefix)
        # logging.debug(files)

        if self.pool_size == 0:
            for fn in files:
                put_inst(fn, dest)
        else:
            p = partial(put_inst,
                        dest=dest.asdict() )
            self.pool.map( p, files )

