import logging
from pprint import pformat
import click
from crud.manager import EndpointManager
from crud.cli.utils import CLICK_MAPPING, import_cmds
from crud.cli.cli import epilog
from diana import __version__
from diana.utils.endpoint.watcher import suppress_watcher_debug
from diana.utils.gateways.requesters import suppress_urllib_debug

__readme_header__ = """\
diana-cli
==================

Derek Merck  
<derek.merck@ufl.edu>  
University of Florida and Shands Hospital  
Gainesville, FL  

[![Build Status](https://travis-ci.org/derekmerck/diana2.svg?branch=master)](https://travis-ci.org/derekmerck/diana2)
[![Coverage Status](https://codecov.io/gh/derekmerck/diana2/branch/master/graph/badge.svg)](https://codecov.io/gh/derekmerck/diana2)
[![Doc Status](https://readthedocs.org/projects/diana/badge/?version=master)](https://diana.readthedocs.io/en/master/?badge=master)

Source: <https://www.github.com/derekmerck/diana2>  
Documentation: <https://diana.readthedocs.io>  
Image:  <https://cloud.docker.com/repository/docker/derekmerck/diana2>

`diana-cli` provides a command-line interface to DIANA endpoints.

## Parameter Types

- MAPPING parameters may be json or yaml format strings, or an `@/file.yaml` path to a json or yaml formatted file.
- ARRAY parameters may be json or yaml format strings, or an `@/file.txt` path to a newline separated list of items.
- ENDPOINT parameters must either exist in the services description, or be a prefixed shortcut such as `path:/data/my_dir`, which would create a DcmDir with `basepath=/data/my_dir`.

## Usage

"""


@click.group(name="diana-cli", chain=True, epilog=epilog)
@click.version_option(version=__version__, prog_name="diana-cli")
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-s', '--services', type=CLICK_MAPPING, default={},
              help="Services dict as yaml/json format string or @file.yaml")
@click.pass_context
def cli(ctx, verbose, services):
    """Run DIANA packages using a command-line interface.

    \b
    $ python3 -m diana.cli.cli --version
    diana-cli, version 2.1.x

    \b
    $ pip3 install python-diana
    $ diana-cli --version
    diana-cli, version 2.1.x

    Also supports chained operations on dixels.  For example, to read a directory and put all instances in a local orthanc:

    \b
    $ diana-cli dgetall path:/data/dcm oput orthanc:

    """

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        click.echo('Verbose mode is ON')
    else:
        logging.basicConfig(level=logging.WARNING)
        suppress_urllib_debug()
    suppress_watcher_debug()

    if verbose:
        click.echo("Using services:")
        click.echo(pformat(services))

    # Runner does not instantiate ctx properly
    if not ctx.obj:
        ctx.obj = {}

    service_mgr = EndpointManager(ep_descs=services)

    ctx.obj['services'] = service_mgr
    ctx.obj['items'] = []



from crud.cli import commands as crud_cmds
import_cmds(cli, crud_cmds)

from diana.cli import commands as diana_cmds
import_cmds(cli, diana_cmds)
import diana.cli.string_descs

from wuphf.cli import commands as wuphf_cmds
import_cmds(cli, wuphf_cmds)
import wuphf.cli.string_descs


# Indirection to set envar prefix from setuptools entry pt
def main():
    cli(auto_envvar_prefix='DIANA', obj={})


if __name__ == "__main__":
    main()
