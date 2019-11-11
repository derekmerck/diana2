from crud.abc import Serializable
from .smtp_messenger import SmtpMessenger


class EmailSMSMessenger(SmtpMessenger):

    relays = {
        "alltel":     "message.alltel.com",
        "att":        "txt.att.net",
        "boost":      "myboostmobile.com",
        "nextel":     "messaging.sprintpcs.com",
        "sprint":     "messaging.sprintpcs.com",
        "t-mobile":   "tmomail.net",
        "uscellular": "email.uscc.net",
        "verizon":    "vtext.com",
        "virgin":     "vmobl.com"
    }

    def _send(self, msg, to_number, carrier=None):
        if carrier.lower() not in self.relays.keys():
            raise ValueError("Unknown carrier: {}".format(carrier))
        to_addr = '%s@%s' % (to_number, self.relays.get(carrier))
        SmtpMessenger._send(self, msg, to_addr)


EmailSMSMessenger.register()
