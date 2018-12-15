import logging, zipfile, os
import attr
from ..dixel import Dixel
from ..utils.endpoint import Watcher, Event
from ..utils.dicom import DicomFormatError, DicomLevel, DicomEvent, DicomUIDMint

@attr.s
class DianaWatcher(Watcher):

    @classmethod
    def move(cls, event, dest, remove=False):
        item = event.event_data
        source = event.event_source
        logging.debug("Moving {}".format(item))

        try:
            item = source.get(item, view="file")
            if remove:
                source.remove(item)
            return dest.put(item)
        except DicomFormatError as e:
            logging.error(e)

    # TODO: Annotate with "anonymized_from" meta for alerts
    @classmethod
    def anonymize_and_move(cls, event, dest, remove=False):
        oid = event.event_data
        source = event.event_source

        item = source.get(oid, level=DicomLevel.INSTANCES)  # Get tags and meta
        item.set_metadata()                                 # Initialize pre-anon metadata
        item = source.anonymize(item, remove=remove)        # Returns dixel with file

        logging.debug("Anonymizing and moving {}".format(item))

        return dest.put(item)

    # TODO: could figure out indexing level automatically
    @classmethod
    def index_series(cls, event, dest,
                     token=None,
                     index=None):
        oid = event.event_data
        source = event.event_source
        item = source.get(oid, level=DicomLevel.SERIES, view="tags")

        logging.debug("Indexing {}".format(item))
        logging.debug("Dest: {}".format(dest))

        return dest.put(item, token=token, index=index, host=event.event_source.location)

    @classmethod
    def index_instance(cls, event, dest,
                     token=None,
                     index=None):
        oid = event.event_data
        source = event.event_source
        item = source.get(oid, level=DicomLevel.INSTANCES, view="tags")

        logging.debug("Indexing {}".format(item))
        logging.debug("Dest: {}".format(dest))

        return dest.put(item, token=token, index=index, host=event.event_source.location)

    @classmethod
    def index_by_proxy(cls, event, dest,
                       anonymize=False,
                       retrieve=False,
                       token=None,
                       index=None):

        item = event.event_data  # This should be a Dixel if a proxied return
        source = event.event_source

        # self.logger.debug("Received event with {} from {}".format(item, source))

        if retrieve:
            item = source.find(item, retrieve=True)
            item = source.get(item, view="tags")
            source.remove(item)

        if anonymize:

            logging.debug(item)
            # TODO: Should jitter datetime if it is important
            item.meta['AccessionNumber'] = md5(item.meta['AccessionNumber'].encode('UTF8')).hexdigest()
            item.meta['PatientID']       = md5(item.meta['PatientID'].encode('UTF8')).hexdigest()
            item.meta['StudyInstanceUID'] = DicomUIDMint().uid()

        return dest.put(item, token=token, index=index, host=event.event_source.location)

    @classmethod
    def unpack_and_put(cls, event, dest, remove=False):
        item_fp = event.event_data

        logging.debug("Unzipping {}".format(item_fp))

        try:
            with zipfile.ZipFile(item_fp) as z:
                for member in z.infolist():
                    logging.debug(member)
                    # member.is_dir() for 3.6 only!
                    if not member.filename.endswith("/"):
                        # read the file
                        logging.debug("Uploading {}".format(member))
                        f = z.read(member)
                        item = Dixel(level=DicomLevel.INSTANCES, file=f)
                        logging.debug(item)
                        dest.put(item)
            if remove:
                os.remove(item_fp)
        except zipfile.BadZipFile as e:
            logging.error(e)

