import logging
import os
import tempfile
import shutil
from crud.abc import Serializable
from diana.apis import *
from diana.cli import cli as app
# from diana_cli.collect2 import Collector2

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

import pytest


@pytest.mark.skip(reason="Need to refactor for automated testing")
def test_collector_cli():

    runner = CliRunner()

    result = runner.invoke(app, ["--verbose", "-s", json.dumps(services), "check"])
    print(result.output)

    assert("pacs: Ready" in result.output)

    result = runner.invoke(app, ["--verbose", "-s", json.dumps(services), "collect2",
                                 "pacs", "path:/tmp", "52682350"])
    print(result.output)
    print(result.exception)


@pytest.mark.skip(reason="Need to refactor for automated testing")
def test_collector(setup_orthanc0, setup_orthanc1, anonymize):

    pacs = Serializable.Factory.create(**services.get("pacs"))
    proxy = Serializable.Factory.create(**services.get("proxy"))
    proxy.clear()

    tmp = "/tmp"
    shutil.rmtree(os.path.join(tmp, "images"), ignore_errors=True)

    meta_dest = CsvFile(fp=os.path.join(tmp, "key.csv"))
    meta_dest.read()

    meta_dest.fieldnames = ["AccessionNumber", "_ShamAccessionNumber",
                            "PatientID", "_ShamID"]

    im_dest = DcmDir(path=os.path.join(tmp, "images"))
    report_dest = None

    c = Collector2(source=pacs,
                   meta=meta_dest,
                   reports=report_dest,
                   images=im_dest)

    h, s, f = c.run(["52682350", "99920000"], anonymize=anonymize)

    print("Failed:  {}".format(f))
    print("Handled: {}".format(h))
    print("Skipped: {}".format(s))

    assert((h, s, f) == (1, 0, 1))

    c.reset()
    h, s, f = c.run(["52682350", "99920000"], anonymize=anonymize)

    print("Failed:  {}".format(f))
    print("Handled: {}".format(h))
    print("Skipped: {}".format(s))

    assert((h,s,f) == (0,1,1))

    proxy.clear()
    shutil.rmtree(os.path.join(tmp, "images"), ignore_errors=True)


if __name__ == "__main__":

    from conftest import mk_orthanc

    logging.basicConfig(level=logging.DEBUG)

    mk_orthanc(8042, 4242, 8043, 4243)
    mk_orthanc(8043, 4243, 8042, 4242)
    # add data

    test_collector(anonymize=False)
    test_collector(anonymize=True)
