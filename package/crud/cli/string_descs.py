import os
from crud.manager import EndpointManager
from crud.endpoints import Splunk


def make_splunk(s):  # splunk:host,user,password,tok,index
    s = s[7:]
    try:
        host, user, password, tok, index = s.split(",")
    except ValueError:
        host = user = password = tok = index = None

    if not host:
        host = os.environ.get("SPLUNK_HOST", "splunk")
    if not user:
        user = os.environ.get("SPLUNK_USER", "admin")
    if not password:
        password = os.environ.get("SPLUNK_PASSWORD", "passw0rd!")
    if not tok:
        tok = os.environ.get("SPLUNK_HEC_TOKEN")
    if not index:
        index = None

    return Splunk(
        host=host,
        index=index,
        user=user,
        password=password,
        hec_token=tok
    )


EndpointManager.add_prefix("splunk:", make_splunk)
