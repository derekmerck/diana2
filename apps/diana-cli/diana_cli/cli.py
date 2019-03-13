import logging, os
import yaml
import click
from . import __version__
from diana.utils.gateways import supress_urllib_debug
from diana import __version__ as diana_version

from .check import check
from .epdo import epdo
from .collect import collect
from .collect2 import collect2
from .dcm2im import dcm2im, dcm2json
from .file_index import findex, fiup
from .guid import guid
from .mock import mock
from .ofind import ofind
from .verify import verify
from .watch import watch

epilog = """
SERVICES is a required platform endpoint description in yaml format.

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


@click.group(name="diana-cli", epilog=epilog)
@click.option('--verbose/--no-verbose', default=False)
@click.version_option(version=(__version__, diana_version),
                      prog_name=("diana-cli", "python-diana"))
@click.option('-s', '--services', type=click.STRING,
              help="Diana service desc as yaml format string")
@click.option('-S', '--services_path', type=click.Path(exists=True),
              help="Diana service desc as a yaml format file or directory of files")
@click.pass_context
def cli(ctx, verbose, services, services_path):
    """Run diana packages using a command-line interface."""

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        # suppress_urllib_debug()
        click.echo('Verbose mode is %s' % ('on' if verbose else 'off'))
    else:
        logging.basicConfig(level=logging.WARNING)
        supress_urllib_debug()

    _services = {}
    if services_path:
        logging.debug("Found services path")
        with open(services_path) as f:
            services_exp = os.path.expandvars(f.read())
            services_in = yaml.safe_load(services_exp)
            _services.update(services_in)

    if services:
        logging.debug("Found services var")
        services_exp = os.path.expandvars(services)
        services_in = yaml.safe_load(services_exp)
        _services.update(services_in)

    # Runner does not instantiate ctx properly
    if not ctx.obj:
        ctx.obj = {}
    ctx.obj['services'] = _services


cmds = [
    check,
    collect,
    collect2,
    dcm2im,
    dcm2json,
    epdo,
    findex,
    fiup,
    guid,
    mock,
    ofind,
    verify,
    watch,
]
for c in cmds:
    cli.add_command(c)


# Indirection to set envar prefix from setuptools entry pt
def main():
    cli(auto_envvar_prefix='DIANA', obj={})


if __name__ == "__main__":
    main()
