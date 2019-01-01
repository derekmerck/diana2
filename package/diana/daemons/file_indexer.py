import glob, os, logging
from multiprocessing import Pool
from functools import partial
import attr
from ..apis import Redis, DcmDir, Orthanc
from ..dixel import DixelView


def index_file(fn, dcm=None, reg=None, prefix=None):

    if not isinstance(dcm, DcmDir):
        dcm = DcmDir(**dcm)
    if not isinstance(reg, Redis):
        reg = Redis(**reg)
    try:
        d = dcm.get(fn, view=DixelView.TAGS)
        reg.register(d, prefix=prefix)
    except:
        logging.warning("Skipping non-DICOM file {}".format(fn))
        pass


def put_inst(fn, dcm, dest):

    if not isinstance(dcm, DcmDir):
        dcm = DcmDir(**dcm)
    if not isinstance(dest, Orthanc):
        dest = Orthanc(**dest)
    d = dcm.get(fn, view=DixelView.FILE)
    dest.put(d)


@attr.s
class FileIndexer(object):
    """Create a registry for all files in a DICOM directory and subdirs"""

    prefix = attr.ib( default="dcmfdx")
    basepath = attr.ib( default="." )
    recurse_style = attr.ib( default="UNSTRUCTURED" )

    registry = attr.ib( type=Redis, default=None, repr=False )
    dest = attr.ib( type=Orthanc, default=None, repr=False )

    pool_size = attr.ib( default=0 )
    pool = attr.ib( init=False, repr=False )
    @pool.default
    def create_pool(self):
        if self.pool_size > 0:
            return Pool(self.pool_size)

    def run_indexer(self, rex="*.dcm"):
        # TODO: need to store subdirectory from base path as well!

        def index_dir(path="."):

            fg = os.path.join(path, rex)
            files = [os.path.basename(x) for x in glob.glob(fg)]
            D = DcmDir(path=path)

            if self.pool_size == 0:
                for fn in files:
                    index_file(fn, D, self.registry, self.prefix)
            else:
                p = partial(index_file,
                            dcm=D.asdict(),
                            reg=self.registry.asdict(),
                            prefix=self.prefix )
                self.pool.map(p, files)

        D = DcmDir(path=self.basepath, recurse_style=self.recurse_style)
        for subdir in D.subdirs():
            index_dir(subdir)


    def run_uploader(self, dest: Orthanc=None):

        def put_accession(accession_number):
            """Can spawn this as a separate process"""

            files = self.registry.registry_item_data(accession_number, prefix=self.prefix)
            logging.debug(files)

            if self.pool_size == 0:
                for fn in files:
                    put_inst(fn, D, dest)
            else:
                p = partial(put_inst,
                            dcm=D.asdict(),
                            dest=dest.asdict() )
                self.pool.map( p, files )

        dest = dest or self.dest
        if not dest:
            raise ValueError("No upload destination provided")
        # TODO: Only for orthanc style
        D = DcmDir(path=self.basepath, subpath_depth=2, subpath_width=2)

        for item in self.registry.registry_items(prefix=self.prefix):
            put_accession(item)
