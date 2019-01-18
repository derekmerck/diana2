import logging
import yaml
import click
import cli_commands
from diana.utils.gateways import supress_urllib_debug
from diana import __version__ as diana_version

__version__ = "2.1.0"

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
                      prog_name=("diana-cli.py", "python-diana"))
@click.option('-s', '--services', type=click.STRING,
              help="Diana service desc as yaml format string")
@click.option('-S', '--services_path', type=click.Path(exists=True),
              help="Diana service desc as a yaml format file or directory of files")
@click.pass_context
def cli(ctx, verbose, services, services_path):
    """Run diana packages using a command-line interface."""

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        # supress_urllib_debug()
        click.echo('Verbose mode is %s' % ('on' if verbose else 'off'))
    else:
        logging.basicConfig(level=logging.WARNING)
        supress_urllib_debug()

    if services:
        click.echo("Found services")
        _services = yaml.load(services)
        click.echo(_services)
    else:
        _services = {}

    if services_path:
        with open(services_path) as f:
            _servicesp = yaml.load(f)
        _services.update(_servicesp)

    # Runner does not instantiate ctx properly
    if not ctx.obj:
        ctx.obj = {}
    ctx.obj['services'] = _services

coms = [
    cli_commands.check,
    cli_commands.collect,
    cli_commands.dcm2im,
    cli_commands.findex,
    cli_commands.fiup,
    cli_commands.guid,
    cli_commands.mock,
    cli_commands.ofind,
    cli_commands.watch
]

for c in coms:
    cli.add_command(c)


if __name__ == '__main__':
    cli(auto_envvar_prefix='DIANA', obj={})