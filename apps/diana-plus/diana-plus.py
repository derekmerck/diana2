import logging
import click
import commands
from diana.utils.gateways import supress_urllib_debug
from diana import __version__ as diana_version

__version__ = "2.0.1"

@click.group(name="diana-plus")
@click.option('--verbose/--no-verbose', default=False)
@click.version_option(version=(__version__, diana_version),
                      prog_name=("diana-plus.py", "python-diana"))
def cli(verbose):
    """Run diana-plus packages using a command-line interface."""

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        supress_urllib_debug()
        click.echo('Verbose mode is %s' % ('on' if verbose else 'off'))
    else:
        logging.basicConfig(level=logging.WARNING)
        supress_urllib_debug()

coms = [
    commands.ssde,
    # commands.classify,
]

for c in coms:
    cli.add_command(c)


if __name__ == '__main__':
    cli(auto_envvar_prefix='DXPLS', obj={})