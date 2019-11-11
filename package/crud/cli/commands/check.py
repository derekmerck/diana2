import click
from crud.abc import Endpoint
from crud.cli.utils import CLICK_ENDPOINT


@click.command(short_help="Check endpoint status")
@click.argument("endpoint", type=CLICK_ENDPOINT)
@click.pass_context
def check(ctx, endpoint: Endpoint):
    """Check endpoint status

    \b
    $ crud-cli check redis
    """
    click.echo(click.style('Check Endpoint Status', underline=True, bold=True))
    avail = endpoint.check()

    s = "{}: {}".format(endpoint.name, "Ready" if avail else "Unavailable")
    if avail:
        click.echo(click.style(s, fg="green"))
    else:
        click.echo(click.style(s, fg="red"))
