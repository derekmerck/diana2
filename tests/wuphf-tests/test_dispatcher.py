import os
import yaml
import logging
from wuphf.endpoints import SmtpMessenger, EmailSMSMessenger
from wuphf.endpoints.smtp_messenger import sample_msg
from wuphf.daemons import Dispatcher

DRYRUN=False

subscriptions = """
---
- name: Alice
  channels: [channel1]
  email: $TEST_EMAIL_RECEIVER

- name: Bob
  channels: [channel2]
  email: $TEST_EMAIL_RECEIVER1

- name: Carl
  channels: [ALL]
  sms: $TEST_SMS_RECEIVER
  carrier: $TEST_SMS_RCV_CARRIER
"""

subscriptions = os.path.expandvars(subscriptions)

import pytest

@pytest.mark.skip(reason="Refactored dispatcher")
def test_dispatch_to_ep():

    m = SmtpMessenger(
        host="smtp.gmail.com",
        port=587,
        user=os.environ.get("TEST_SMTP_USER"),
        password=os.environ.get("TEST_SMTP_PASSWORD"),
        tls=True,
        msg_t=sample_msg
    )
    m.check()

    n = EmailSMSMessenger(
        host="smtp.gmail.com",
        port=587,
        user=os.environ.get("TEST_SMTP_USER"),
        password=os.environ.get("TEST_SMTP_PASSWORD"),
        tls=True,
        msg_t=sample_msg
    )

    dispatcher = Dispatcher(smtp_messenger=m, sms_messenger=n)

    subs = yaml.load(subscriptions)
    for s in subs:
        dispatcher.add_subscriber(s)

    dispatcher.put(channels=["channel0"], data={"msg_text": "Hello0"})
    dispatcher.put(channels=["channel1"], data={"msg_text": "Hello1"})
    dispatcher.put(channels=["CHANNEL2"], data={"msg_text": "Hello2"})
    dispatcher.put(channels=["ALL"], data={"msg_text": "Hello3"})
    # TODO: Send to "ALL" doesn't work!
    dispatcher.put(channels=["channel0", "channel1", "channel2"], data={"msg_text": "Hello4"})

    dispatcher.handle_queue(dryrun=DRYRUN)

    # Should result in:
    #   - Hello0 -> TEST_SMS_RECEIVER (all)
    #   - Hello1 -> TEST_EMAIL_RECEIVER, TEST_SMS_RECEIVER
    #   - Hello2 -> TEST_EMAIL_RECEIVER1, TEST_SMS_RECEIVER
    #   - Hello3 -> TEST_EMAIL_RECEIVER, TEST_EMAIL_RECEIVER1, TEST_SMS_RECEIVER
    #   - Hello4 -> TEST_EMAIL_RECEIVER, TEST_EMAIL_RECEIVER1, TEST_SMS_RECEIVER


@pytest.mark.skip(reason="Refactored dispatcher")
def test_dispatcher():

    subs = yaml.load(subscriptions)
    print(subs)

    dispatcher = Dispatcher()
    for s in subs:
        dispatcher.add_subscriber(s)

    dispatcher.put(channels=["channel0"], data="Hello0")
    dispatcher.put(channels=["channel1", "CHANNEL2"], data="Hello1")
    dispatcher.put(channels=["ALL"], data="Hello1")

    dispatcher.handle_queue()


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    # test_dispatcher()
    test_dispatch_to_ep()

