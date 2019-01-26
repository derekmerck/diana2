import logging
import click
from . import classify, ssde
from diana.utils.gateways import supress_urllib_debug
from diana_cli import __version__
from diana import __version__ as diana_version


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
    ssde,
    classify,
]

for c in coms:
    cli.add_command(c)


# Indirection to set envar prefix from setuptools entry pt
def main():
    cli(auto_envvar_prefix='DIANA', obj={})


if __name__ == "__main__":
    main()
