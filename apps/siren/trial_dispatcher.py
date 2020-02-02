import attr
from wuphf.daemons import Dispatcher, Subscriber, Sender

channel_tags = {}

@attr.s
class TrialSender(Sender):
    trial = attr.ib()
    site = attr.ib()

@attr.s
class TrialSubscriber(Subscriber):
    affiliation = attr.ib()

@attr.s
class TrialDispatcher(Dispatcher):
    """Includes logic to expand trial and site names from short tags on folders"""

    channel_tags = attr.ib(default=dict)

    def add_subscribers(self, subscribers):
        for s in subscribers:
            s["affiliation"] = self.channel_tags.get(s["affiliation"])
            self.add_subscriber(TrialSubscriber(**s))

    def put(self, item, dryrun=False):
        """Project specific inference for sender and channels"""

        # May receive data as a mapping {"meta": ..., "data": ...} or a serializable item
        if hasattr(item, "asdict"):
            item = item.asdict()

        trial = item["meta"]["signature"]["trial"]
        site = item["meta"]["signature"]["site"]
        channels = [trial, site, f"{trial}-{site}"]
        trial_name = self.channel_tags.get(trial)
        site_name = self.channel_tags.get(site)
        sender = TrialSender(trial=trial_name, site=site_name)
        sent = super().put(item, sender, channels, dryrun=dryrun)
        return sent

