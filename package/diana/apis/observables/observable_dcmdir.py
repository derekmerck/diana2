import logging, os
import time
import attr
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from .. import DcmDir
from ...utils.dicom import DicomEventType
from ...utils.endpoint import Event, ObservableMixin

@attr.s
class ObservableDcmDir(DcmDir, ObservableMixin):
    """
    DcmDir service that implements a watchdog polling system and converts
    file events into DicomEvents.
    """
    name = attr.ib(default="ObsDcmDir")

    def changes(self):
        pass

    @attr.s(hash=False)
    class WatchdogEventReceiver(FileSystemEventHandler):
        source = attr.ib()

        def on_any_event(self, wd_event: FileSystemEvent):

            logger = logging.getLogger(self.source.name + "-Rcv")
            logger.debug(wd_event)

            if wd_event.is_directory:
                return

            event_data = wd_event.src_path
            event_type = None
            sleep_time = 1.0

            # TODO: Should actually create multiple events, or
            #  include multiple tyupes for each: study/series added and instance added

            if wd_event.event_type == "created" and event_data.endswith(".zip"):
                logger.debug("Found a zipped archive")
                event_type = DicomEventType.FILE_ADDED
                sleep_time = 1.0  # Wait 1 sec for file to settle

            elif wd_event.event_type == "created":
                logger.debug("Found a possible dcm instance")
                event_type = DicomEventType.FILE_ADDED
                sleep_time = 0.2  # Wait 0.2 secs for file to settle

            if event_type:

                # Poll for a while until file is stable
                size = os.stat(event_data).st_size
                prev_size = size - 1
                while size > prev_size:
                    time.sleep(sleep_time)  # No change in this long
                    prev_size = size
                    size = os.stat(event_data).st_size
                logger.debug("Final file size: {}".format(size))

                e = Event(
                    evtype=event_type,
                    source_id=self.source.epid,
                    data={event_data}
                )
                logger.debug('Accepting file event {}'.format(event_data))
                self.source.event_queue.put(e)

            else:
                logger.debug('Rejecting non-creation event {}'.format(wd_event))


    def poll_events(self):

        observer = Observer()
        receiver = self.WatchdogEventReceiver(source=self)

        observer.schedule(receiver, self.path, recursive=True)
        observer.start()

        self.proc = observer  # For kill on __del__
