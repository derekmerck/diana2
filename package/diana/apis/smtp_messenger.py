"""
Render a message from item.meta using Jinja templates and send via smtp
"""
import logging
import smtplib
import attr
from ..utils.endpoint import Endpoint
from ..utils import render_template

sample_msg = """
To: {{ to_addrs }}
From: {{ from_addr }}
Subject: Sample message generated on {{ now().date() }}

The message is: "{{ msg_text }}"
"""


@attr.s
class SMTPMessenger(Endpoint):

    host = attr.ib(default="smtp.example.com")
    port = attr.ib(default=22)
    user = attr.ib(default="admin")
    password = attr.ib(default="passw0rd!")

    from_addr = attr.ib()

    @from_addr.default
    def set_from_addr(self):
        return "{}@{}".format(self.user, self.host)

    to_addrs = attr.ib(default=None)
    msg_t = attr.ib(default=None)

    def check(self):
        gateway = smtplib.SMTP(self.host, self.port)
        gateway.set_debuglevel(1)
        gateway.close()

    def get(self, item, to_addrs=None, from_addr=None, msg_t=None) -> str:

        if not from_addr:
            from_addr = self.from_addr
        if not from_addr:
            raise ValueError("No 'from' address provided")
        if not to_addrs:
            to_addrs = self.to_addrs
        if not to_addrs:
            raise ValueError("No 'to' address provided")
        if not msg_t:
            msg_t = self.msg_t
        if not msg_t:
            raise ValueError("No message template provided")

        if hasattr(item, 'meta'):
            data = item.meta
        elif isinstance(item, dict):
            data = item
        else:
            raise TypeError("Cannot convert {} to mapping")

        msg = render_template(msg_t, **data, from_addr=from_addr, to_addrs=to_addrs )

        return msg

    def send(self, item, to_addrs=None, from_addr=None, msg_t=None, dryrun=False):

        msg = self.get(item, to_addrs=to_addrs, from_addr=from_addr, msg_t=msg_t)

        logger = logging.getLogger(self.name)
        logger.info("Sending message via SMTP connector:\n{}".format(msg))

        if not dryrun:
            gateway = smtplib.SMTP(self.host, self.port)
            gateway.set_debuglevel(1)
            gateway.sendmail(from_addr, to_addrs, msg)
            gateway.close()
        else:
            logger.info("Declining to submit message to gateway (dryrun)")
