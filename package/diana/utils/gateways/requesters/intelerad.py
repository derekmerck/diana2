import logging
from pprint import pformat
from hashlib import sha1
import attr
from .requester import Requester
from crud.exceptions import GatewayConnectionError
from ...dicom import DicomLevel


@attr.s
class Intelerad(Requester):
    """Diana-agnostic API and helpers for Intelerad, with no endpoint or dixel dependencies."""

    name = attr.ib(default="InteleradGateway")
    port = attr.ib(default=443)
    user = attr.ib(default="")
    password = attr.ib(default="")
    protocol = attr.ib(default="https")

    def find(self, phrase):
        headers = {"content-type": "application/json"}

        data = {
            "data": [
                {
                    "params": {
                        "input": {
                            "ws165": "{}".format(phrase),
                            "ws26.db": "timeSearch",
                            "ws26.type": "rel",
                            "ws26.start": "2024-08-09",
                            "ws26.timestart": "12:00 AM"
                        },
                        "type": "advanced",
                        "isCountOnly": False,
                        "limit": None
                    },
                    "call": "search/Exam.search",
                    "sort": [
                        {
                            "property": "defaultDirectSorting",
                            "direction": "DESC"
                        }
                    ],
                    "operation": "user",
                    "page": 1,
                    "start": 0,
                    "limit": "50"
                }
            ],
            "app": "workflow",
            "action": "rpc",
            "method": "search"
        }

        return self._post(resource="rpc/app.php?app=workflow^&sysClient=^", headers=headers, json=data)

    def login(self):
        headers = {"content-type": "application/json"}

        data = {
            "data": [
                {
                    "params": {
                        "input": {
                            "ws165": "{}".format(phrase),
                            "ws26.db": "timeSearch",
                            "ws26.type": "rel",
                            "ws26.start": "2024-08-09",
                            "ws26.timestart": "12:00 AM"
                        },
                        "type": "advanced",
                        "isCountOnly": False,
                        "limit": None
                    },
                    "call": "search/Exam.search",
                    "sort": [
                        {
                            "property": "defaultDirectSorting",
                            "direction": "DESC"
                        }
                    ],
                    "operation": "user",
                    "page": 1,
                    "start": 0,
                    "limit": "50"
                }
            ],
            "app": "workflow",
            "action": "rpc",
            "method": "search"
        }

        return self._post(resource="rpc/app.php?app=login&sysClient=", headers=headers, json=data)