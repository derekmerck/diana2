# generic crud-cli version 2

import sys
import os
import logging
import click
import attr

from ..import __version__
from ..manager import EndpointManager

# Any command imports must be made here as well?
from pprint import pformat
import yaml

from .utils import CLICK_MAPPING


epilog = """
SERVICES is a required platform endpoint description in json/yaml format.

\b
---
orthanc:
  ctype: Orthanc
  port: 8042
  host: my_orthanc
redis:
  ctype: Redis
...
"""


@click.group(name="crud-cli", epilog=epilog, chain=True)
@click.version_option(version=__version__, prog_name="crud-cli")
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-s', '--services', type=CLICK_MAPPING, default={},
              help="Services dict as yaml/json format string or @file.yaml")
@click.pass_context
def cli(ctx, verbose, services):
    """Run diana packages using a command-line interface."""

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        click.echo('Verbose mode is ON')
    else:
        logging.basicConfig(level=logging.WARNING)

    if verbose:
        click.echo("Using services:")
        click.echo(pformat(services))

    # Runner does not instantiate ctx properly
    if not ctx.obj:
        ctx.obj = {}

    service_mgr = EndpointManager(ep_descs=services)

    ctx.obj['services'] = service_mgr
