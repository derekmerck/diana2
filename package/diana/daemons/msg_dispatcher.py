import attr
from diana.utils.endpoint import Dispatcher, Subscription
from diana.apis import SMTPMessenger

@attr.s
class MessageSubscription(Subscription):

    project = attr.ib()
    site = attr.ib()
    dest_name = attr.ib()
    dest_addr = attr.ib()
    messenger = attr.ib(type=SMTPMessenger)

    def listening_for(self, event):
        return self.project == event.meta.project and \
               ( self.site == event.meta.site or \
                 self.site == "ALL" )

    def callback_for(self, event):
        self.messenger.send(event, to_addrs=self.dest_addr, **event.meta)


def read_special_val(value):
    if value.startswith("@"):
        fn = value[1:]
        with open(fn) as f:
            value = f.read()
    return value


@attr.s
class ProjectDispatcher(Dispatcher):

    smpt_host = attr.ib(default=None)
    smpt_user = attr.ib(default=None)
    msg_t = attr.ib(default=None, converter=read_special_val)

    messenger = SMTPMessenger(smpt_host, smpt_user, msg_t)

    project_data = attr.ib(default=None, converter=read_special_val)

    subscriptions = attr.ib(init=False)
    @subscriptions.default
    def create_project_subscriptions(self):
        subs = []

        for site in self.project_data["sites"]:
            for dest in site:
                sub = MessageSubscription(
                    project = self.project_data["project"]["name"],
                    site = site.name,
                    dest_addr = dest.addr,
                    dest_name = dest.name,
                    messenger = self.messenger
                )

        return subs



