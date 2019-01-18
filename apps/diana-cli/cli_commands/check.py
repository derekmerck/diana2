import click
from diana.utils import Serializable
# importing all apis allows them to be immediately deserialized
from diana.apis import *

@click.command(short_help="Check endpoint status")
@click.argument('endpoints', nargs=-1)
@click.pass_context
def check(ctx, endpoints):
    """Survey status of service ENDPOINTS"""
    services = ctx.obj.get('services')
    click.echo('Checking endpoint status')
    click.echo('------------------------')

    if not endpoints or endpoints=="ALL":
        endpoints = services.keys()

    for ep_key in endpoints:
        ep = Serializable.Factory.create(**services.get(ep_key))
        click.echo("{}: {}".format( ep_key, "Ready" if ep.check() else "Not Ready" ))
