import os
import logging
from wuphf.endpoints import SmtpMessenger, SlackMessenger, EmailSMSMessenger
from wuphf.endpoints.smtp_messenger import sample_msg

DRYRUN = True

import pytest

@pytest.mark.skip(reason="No way to check response automatically")
def test_smtp_messenger(capsys):

    m = SmtpMessenger(
        host="smtp.gmail.com",
        port=587,
        user=os.environ.get("TEST_SMTP_USER"),
        password=os.environ.get("TEST_SMTP_PASSWORD"),
        tls=True,
        msg_t=sample_msg
    )
    m.check()

    to_addr = os.environ.get("TEST_EMAIL_RECEIVER")
    m.send({"msg_text": "Have a great day!"}, to_addr, dryrun=DRYRUN)

    exp1 = """The message is: "Have a great day"""

    if capsys:
        captured = capsys.readouterr()
        assert exp1 in captured.out


@pytest.mark.skip(reason="No way to check response automatically")
def test_email_sms_messenger():

    m = EmailSMSMessenger(
        host="smtp.gmail.com",
        port=587,
        user=os.environ.get("TEST_SMTP_USER"),
        password=os.environ.get("TEST_SMTP_PASSWORD"),
        tls=True,
        msg_t=sample_msg
    )
    m.check()

    to_number = os.environ.get('TEST_SMS_RECEIVER')
    carrier = os.environ.get('TEST_SMS_RCV_CARRIER')
    m.send({"msg_text": "Have a great day!"}, to_number, carrier=carrier)


@pytest.mark.skip(reason="No way to check response automatically")
def test_twilio_messenger():

    m = TwilioMessenger(
        account_sid=os.environ.get("TWILIO_ACCOUNT_SID"),
        auth_token=os.environ.get("TWILIO_AUTH_NUMBER"),
        from_number=os.environ.get("TWILIO_FROM_NUMBER")
    )

    to_number = os.environ.get("SMS_TEST_NUMBER")
    m.send('Have a great day!', to_number)


@pytest.mark.skip(reason="No way to check response automatically")
def test_slack_messenger():

    m = SlackMessenger(url=os.environ.get("SLACK_URL"))
    m.send('Have a great day!')


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    # test_smtp_messenger()
    test_email_sms_messenger()
    # test_twilio_messenger()
    # test_slack_messenger()
