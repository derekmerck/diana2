import click
from diana.utils import Serializable
# importing these classes allows them to be immediately deserialized
from diana.endpoints import Orthanc, Redis, DcmDir

@click.command()
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

