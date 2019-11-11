# TODO: Needs a queue and run function so it can serve as a daemon thread vs in a loop??

import attr
from typing import List, Mapping
from ..endpoints import ScreenMessenger


@attr.s
class Subscriber:
    name = attr.ib(type=str)
    channels = attr.ib(type=List)
    email = attr.ib(type=str)

    def listening_to(self, _channels) -> bool:
        for c in _channels:
            if c in self.channels:
                return True

    def get_transport(self):
        if self.email:
            return "email", self.email

@attr.s
class Sender:
    pass


@attr.s
class Dispatcher:

    subscribers = attr.ib(factory=list)

    def add_subscriber(self, subscriber: Subscriber):
        self.subscribers.append(subscriber)

    email_messenger = attr.ib(factory=ScreenMessenger)

    def get_messenger(self, type):
        if type == "email" and self.email_messenger:
            return self.email_messenger
        raise RuntimeError(f"No such messenger: {type}")

    def put(self, item, sender, channels, dryrun=False) -> List:  # Returns list of sent items and msgs if successful
        sent = []
        for subscriber in self.subscribers:
            if subscriber.listening_to(channels):
                job = self.send(item, sender, subscriber, dryrun=dryrun)
                if job:
                    sent.append(job)
        return sent

    def send(self, item, sender, receiver, dryrun=False) -> Mapping:  # Returns sent item and msg if successful
        wrapped_item = {
            "item": item,
            "sender": attr.asdict(sender),
            "recipient": attr.asdict(receiver),
        }

        transport, target = receiver.get_transport()

        if transport and target:
            messenger = self.get_messenger(transport)
            msg = messenger.send(wrapped_item, target=target, dryrun=dryrun)

            wrapped_item["msg"] = msg
            return wrapped_item

