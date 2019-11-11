import os
from crud.manager import EndpointManager
from wuphf.endpoints import SmtpMessenger

def make_gmail(s):  # gmail:user,password
    s = s[6:]
    try:
        user, password = s.split(",")
    except:
        user = password = None
    if not user:
        user = os.environ.get("GMAIL_USER")
    if not password:
        password = os.environ.get("GMAIL_APP_PASSWORD")
    return SmtpMessenger(
        host="smtp.gmail.com",
        port=587,
        tls="true",
        user=user,
        password=password
    )
EndpointManager.add_prefix("gmail:", make_gmail)
