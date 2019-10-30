import os
from crud.manager import EndpointManager
from diana.apis import Orthanc, DcmDir, Montage

def make_orthanc(s):  # orthanc:user,password,host,port
    s = s[8:]
    try:
        user, password, host, port = s.split(",")
    except ValueError:
        host = password = user = port = None

    if not user:
        user = os.environ.get("ORTHANC_USER", "orthanc")
    if not password:
        password = os.environ.get("ORTHANC_PASSWORD", "passw0rd!")
    if not host:
        host = os.environ.get("ORTHANC_HOST", "localhost")
    if not port:
        port = os.environ.get("ORTHANC_PORT", 8042)

    return Orthanc(
        user=user,
        password=password,
        host=host,
        port=port
    )

EndpointManager.add_prefix("orthanc:", make_orthanc)


def make_dcmdir(s):  # path:/data/this/that
    path = s[5:]     # remove "path:" prefix
    return DcmDir(path=path)

EndpointManager.add_prefix("path:", make_dcmdir)
