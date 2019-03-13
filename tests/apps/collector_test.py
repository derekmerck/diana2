import logging
import os
import tempfile
from diana.utils.endpoint import Serializable
from diana.apis import *
from diana_cli import app
from diana_cli.collect2 import Collector2

from click.testing import CliRunner
import json


services = {
    "proxy": {
        "ctype": "Orthanc"
    },
    "pacs": {
        "ctype": "ProxiedDicom",
        "proxy_desc": {
            "ctype": "Orthanc",
            "aet":   "ORTHANC4242"
        },
        "proxy_domain": "mod0"
    }
}


def test_collector_cli():

    runner = CliRunner()

    result = runner.invoke(app, ["--verbose", "-s", json.dumps(services), "check"])
    print(result.output)

    assert("pacs: Ready" in result.output)

    result = runner.invoke(app, ["--verbose", "-s", json.dumps(services), "collect2",
                                 "pacs", "path:/tmp", "100000", "100001"])
    print(result.output)
    print(result.exception)


def test_collector():

    pacs = Serializable.Factory.create(**services.get("pacs"))
    proxy = Serializable.Factory.create(**services.get("proxy"))
    proxy.clear()

    tmp = "/tmp"

    meta_dest = CsvFile(fp=os.path.join(tmp, "meta", "key.csv"))
    im_dest = DcmDir(path=os.path.join(tmp, "images"))
    report_dest = None

    c = Collector2(source=pacs,
                   meta=meta_dest,
                   reports=report_dest,
                   images=im_dest)

    h, s, f = c.run(["52682350"], anonymize=True)

    print("Failed:  {}".format(f))
    print("Handled: {}".format(h))
    print("Skipped: {}".format(s))

    # c.reset()
    # h, s, f = c.run(["52682350", "99920000"])
    #
    # print("Failed:  {}".format(f))
    # print("Handled: {}".format(h))
    # print("Skipped: {}".format(s))


if __name__ == "__main__":

    from conftest import mk_orthanc

    logging.basicConfig(level=logging.DEBUG)

    mk_orthanc(8042, 4242, 8043, 4243)
    mk_orthanc(8043, 4243, 8042, 4242)
    # add data
    test_collector()
