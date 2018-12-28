import logging
import yaml
import click
import commands
from diana.utils.gateways import supress_urllib_debug
from diana import __version__ as diana_version

__version__ = "2.0.1"

@click.group(name="diana-cli")
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
        supress_urllib_debug()
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


cli.add_command(commands.check)
cli.add_command(commands.ofind)
cli.add_command(commands.index)
cli.add_command(commands.indexed_pull)
cli.add_command(commands.dcm2im)
cli.add_command(commands.mock)
cli.add_command(commands.watch)


if __name__ == '__main__':
    cli(auto_envvar_prefix='DIANA', obj={})