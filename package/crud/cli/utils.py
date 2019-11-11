import logging
from typing import List, Mapping
import click
from crud.abc import Endpoint
from crud.utils import deserialize_dict, deserialize_array
from crud.exceptions import EndpointFactoryException


def import_cmds(cli, cmds):
    for item in dir(cmds):
        if not item.startswith("__"):
            cmd = getattr(cmds, item)
            cli.add_command(cmd)


class ClickMapping(click.ParamType):
    name = "mapping"

    def convert(self, value, param, ctx) -> Mapping:
        # print(f"Kwargs is {value}")
        if not value:
            return {}
        try:
            return deserialize_dict(value)
        except TypeError:
            self.fail(f"{value!r} is not a valid dict description", param, ctx)


class ClickArray(click.ParamType):
    name = "array"

    def convert(self, value, param, ctx) -> List:
        if not value:
            return []
        try:
            return deserialize_array(value)
        except TypeError:
            self.fail(f"{value!r} is not a valid array description", param, ctx)


class ClickEndpoint(click.ParamType):
    name = "endpoint"

    def __init__(self, expects=None):
        super().__init__()
        self.expects = expects

    def convert(self, value, param, ctx) -> Endpoint:
        if not value:
            return None
        try:
            services = ctx.obj.get("services")
            logging.debug("Found services")
            if not services:
                raise RuntimeError("No service manager available")
            ep = services.get(value)
            if self.expects and not isinstance(ep, self.expects):
                raise TypeError(f'Service {value!r} is wrong type')
            return ep

        except RuntimeError:
            self.fail(f"Exception creating endpoint {value!r}", param, ctx)
        except (ValueError, EndpointFactoryException):
            self.fail(f"{value!r} is not a valid endpoint", param, ctx)
        except TypeError:
            self.fail(f"{value!r} is not of expected type {self.expects.__name__}", param, ctx)


CLICK_MAPPING = ClickMapping()
CLICK_ARRAY = ClickArray()
CLICK_ENDPOINT = ClickEndpoint()