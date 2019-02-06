
import click
from pprint import pformat
from diana.utils.endpoint import Serializable
from diana.apis import *


@click.command(short_help="Call endpoint method")
@click.argument('method', type=click.STRING)
@click.argument('endpoint', type=click.STRING)
# @click.option('kwargs')
@click.pass_context
def epdo(ctx, method, endpoint):
    """Call METHOD on ENDPOINT.  For example, 'diana-cli epdo info orthanc'."""
    services = ctx.obj.get('services')

    click.echo(click.style('Checking endpoint info', underline=True, bold=True))

    if not services.get(endpoint):
        click.echo(click.style("No such service {}".format(endpoint), fg="red"))
        exit(1)

    ep = Serializable.Factory.create(**services[endpoint])
    if hasattr(ep, method):
        out = ep.__call__(method)

        if out:
            click.echo(pformat(out))
        else:
            click.echo(click.style("No response", fg="red"))
            exit(2)
