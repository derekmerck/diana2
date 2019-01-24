import click
from diana.utils import Serializable
from pprint import pformat
# importing all apis allows them to be immediately deserialized
from diana.apis import *


@click.command(short_help="Check endpoint status")
@click.argument('endpoints', nargs=-1)
@click.pass_context
def check(ctx, endpoints):
    """Survey status of service ENDPOINTS"""
    services = ctx.obj.get('services')

    click.echo(click.style('Services', underline=True, bold=True))
    click.echo(pformat(services))
    click.echo()

    click.echo(click.style('Checking endpoint status', underline=True, bold=True))

    if not endpoints or endpoints=="ALL":
        endpoints = services.keys()

    for ep_key in endpoints:
        ep = Serializable.Factory.create(**services.get(ep_key))
        try:
            ready = ep.check()
            out = click.style("{}: {}".format(ep_key, "Ready" if ready else "Not Ready"),
                              fg="green" if ready else "red")
        except NotImplementedError:
            out = click.style("{}: {}".format(ep_key, "Unimplemented health check"),
                              fg="yellow")
        click.echo(out)


@click.command
def _():
    pass
