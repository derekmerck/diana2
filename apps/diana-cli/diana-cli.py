import click
import yaml
import logging
import commands
from diana.utils.gateways import supress_urllib_debug


@click.group()
@click.option('--verbose/--no-verbose', default=False)
@click.option('-s', '--services', type=click.STRING)
@click.option('-S', '--services_path', type=click.Path(exists=True))
@click.pass_context
def cli(ctx, verbose, services, services_path):
    click.echo('DIANA cli')
    click.echo('Verbose mode is %s' % ('on' if verbose else 'off'))

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        supress_urllib_debug()
    else:
        logging.basicConfig(level=logging.WARNING)
        supress_urllib_debug()

    if services:
        _services = yaml.load(services)
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
cli.add_command(commands.mock)


if __name__ == '__main__':
    cli(obj={})