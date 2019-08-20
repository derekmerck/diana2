import logging
import datetime
import os
import pytest
from diana.apis import SMPTMessenger
from diana.apis.smtp_messenger import sample_msg

exp0 = "To: abc@example.com\nFrom: admin@smtp.example.com\nSubject: Sample message generated on {}".format(datetime.datetime.now().date())
exp1 = "The message is: \"Hello world\""
exp2 = "The message is: \"Foo Bar Baz\""


def test_messenger_template():

    M = SMPTMessenger(msg_t=sample_msg, to_addrs="abc@example.com")

    msg = M.get({"msg_text": "Hello world"})

    assert exp0 in msg
    assert exp1 in msg

    class Item(object):
        def __init__(self, msg_text):
            self.meta = {"msg_text": msg_text}

    item = Item("Foo Bar Baz")

    msg = M.get(item)

    assert exp0 in msg
    assert exp2 in msg


@pytest.mark.skip(reason="No way to check response automatically")
def test_messenger_stmp():

    M = SMPTMessenger(
        msg_t=sample_msg,
        host=os.environ.get("SMTP_HOST"),
        port=os.environ.get("SMTP_PORT"),
        from_addr=os.environ.get("SMTP_FROM_ADDR"),
        to_addrs=os.environ.get("SMTP_TO_ADDRS")
    )

    assert M.check()

    M.send({"msg_text": "Hello world"})


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_messenger_template()
