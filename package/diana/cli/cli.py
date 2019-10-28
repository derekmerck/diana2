import logging
import click
from crud.manager import EndpointManager
from crud.cli.utils import CLICK_MAPPING, import_cmds
from crud.cli.cli import epilog
from diana import __version__
from diana.utils.endpoint.watcher import suppress_watcher_debug
from diana.utils.gateways.requesters import suppress_urllib_debug


@click.group(name="diana-cli", chain=True, epilog=epilog)
@click.version_option(version=__version__, prog_name="diana-cli")
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-s', '--services', type=CLICK_MAPPING,
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
        suppress_watcher_debug()
    else:
        logging.basicConfig(level=logging.WARNING)
        suppress_urllib_debug()

    if verbose:
        click.echo("Using services: {}".format(services))

    # Runner does not instantiate ctx properly
    if not ctx.obj:
        ctx.obj = {}

    service_mgr = EndpointManager(services)

    ctx.obj['services'] = service_mgr

from crud.cli import commands as crud_cmds
import_cmds(cli, crud_cmds)

from diana.cli import commands as diana_cmds
import_cmds(cli, diana_cmds)
import diana.cli.string_descs

try:
    from wuphf.cli import commands as wuphf_cmds
    import_cmds(cli, wuphf_cmds)
    import wuphf.cli.string_descs
except ImportError:
    pass


# Indirection to set envar prefix from setuptools entry pt
def main():
    cli(auto_envvar_prefix='DIANA', obj={})


if __name__ == "__main__":
    main()
