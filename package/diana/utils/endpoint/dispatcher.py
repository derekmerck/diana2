import logging, time
from itertools import count
from datetime import datetime, timedelta
from multiprocessing import Queue
import attr
from . import Endpoint

# Alternate observable pattern:
#
# 1. Receivers subscribe conditional callbacks with the dispatcher
# 2. Events arrive
# 3. Dispatcher checks every subscriber for a match
# 4.   Any matches get use a common callback

@attr.s
class Subscription(object):

    n_items = count(0)
    subid = attr.ib(init=False, factory=n_items.__next__)

    def listening_for(self, event) -> bool:
        return True

    def callback_for(self, event):
        print("Subscriber {} received event {}".format(self.subid, event))


@attr.s
class Dispatcher(Endpoint):

    action_interval = attr.ib(default=1.0)
    event_queue = attr.ib( factory = Queue, init=False )
    subscribers = attr.ib( factory = list, init=False )

    def run(self):

        logger = logging.getLogger("Dispatcher")
        logger.debug("Running")

        while True:
            logger.debug("Checking queues")

            tic = datetime.now()

            while not self.event_queue.empty():
                event = self.event_queue.get()

                for subscription in self.subscribers:
                    if subscription.listening_for(event):
                        subscription.callback_for(event)

            toc = datetime.now()
            if toc - tic < timedelta(seconds=self.action_interval):
                time.sleep(self.action_interval - (toc - tic).seconds)