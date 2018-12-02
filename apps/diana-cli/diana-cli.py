import click
import yaml
import logging
from package.diana.utils import Serializable
from package.diana.endpoints import Orthanc, Redis

@click.group()
@click.option('--verbose/--no-verbose', default=False)
@click.option('-s', '--services', default=None)
@click.option('-S', '--services_path', type=click.Path(exists=True), default=None)
@click.pass_context
def cli(ctx, verbose, services, services_path):
    click.echo('DIANA cli')
    click.echo('Verbose mode is %s' % ('on' if verbose else 'off'))

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if services_path:
        with open(services_path) as f:
            services = yaml.load(f)
            # Runner does not instantiate ctx properly
            if not ctx.obj:
                ctx.obj = {}
            ctx.obj['services'] = services


@cli.command()
@click.argument('endpoints', default=None, nargs=-1)
@click.pass_context
def check(ctx, endpoints):
    services = ctx.obj.get('services')
    click.echo('Checking endpoint status')
    click.echo('------------------------')

    if not endpoints:
        endpoints = services.keys()

    for ep_key in endpoints:
        ep = Serializable.Factory.create(**services.get(ep_key))
        click.echo("{}: {}".format( ep_key, "Ready" if ep.check() else "Not Ready" ))


if __name__ == '__main__':
    cli(obj={})