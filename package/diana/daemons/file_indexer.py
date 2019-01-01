import glob, os, logging
from multiprocessing import Pool
import attr
from ..apis import Redis, DcmDir, Orthanc
from ..dixel import DixelView


@attr.s
class FileIndexer(object):
    """Create a registry for all files in a DICOM directory and subdirs"""

    prefix = attr.ib( default="dcmfdx")
    basepath = attr.ib( default="." )
    recurse_style = attr.ib( default="UNSTRUCTURED" )

    registry = attr.ib( type=Redis, default=None, repr=False )
    dest = attr.ib( type=Orthanc, default=None, repr=False )

    pool_size = attr.ib( default=0 )
    procs = attr.ib( init=False, repr=False )
    @procs.default
    def create_pool(self):
        if self.pool_size > 0:
            return Pool(self.pool_size)

    def run_indexer(self, rex="*.dcm"):

        def index_dir(path="."):
            """Can spawn this as a separate process"""

            fg = os.path.join(path, rex)
            files = [os.path.basename(x) for x in glob.glob(fg)]
            D = DcmDir(path=path)

            def index_file(fn):
                try:
                    d = D.get(fn, view=DixelView.TAGS)
                    self.registry.register(d, prefix=self.prefix)
                except:
                    logging.warning("Skipping non-DICOM file {}".format(fn))
                    pass

            if self.pool_size == 0:
                for fn in files:
                    index_file(fn)
            else:
                self.procs.map(index_file, files)


        D = DcmDir(path=self.basepath, recurse_style=self.recurse_style)
        for subdir in D.subdirs():
            index_dir(subdir)


    def run_uploader(self, dest: Orthanc=None):

        def put_accession(accession_number):
            """Can spawn this as a separate process"""

            files = self.registry.registry_item_data(accession_number)

            def put_inst(fn):
                d = D.get(fn, view=DixelView.FILE)
                dest.put(d)

            if self.pool_size == 0:
                for fn in files:
                    put_inst(fn)
            else:
                self.procs.map( put_inst, files )

        dest = dest or self.dest
        if not dest:
            raise ValueError("No upload destination provided")
        D = DcmDir()

        for item in self.registry.registry_items(prefix=self.prefix):
            put_accession(item)
