import logging
import click
from crud.abc import Endpoint
from crud.manager import EndpointManager
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


@click.command(short_help="Check all endpoints status")
@click.pass_context
def check_all(ctx):
    """Check all endpoints status

    Useful when chained with "print" or "put" as a scheduled heartbeat action.

    \b
    $ diana-cli -s "{redis: {ctype: Redis}, orthanc: {ctype: Orthanc}}" check-all print
    -----------------
    Check All Endpoints Status:
    redis: OK
    orthanc: Unavailable
    -----------------
    Printing Items:
    {'redis': 'OK', 'orthanc': 'Unavailable'}

    """
    click.echo(click.style('Check All Endpoints Status', underline=True, bold=True))

    services: EndpointManager = ctx.obj.get("services")
    logging.debug("Found services")
    if not services:
        raise RuntimeError("No service manager available")

    items = {}
    for endpoint in services.get_all():
        avail = endpoint.check()
        items[endpoint.name] = "Ready" if avail else "Unavailable"
        s = "{}: {}".format(endpoint.name, "Ready" if avail else "Unavailable")
        if avail:
            click.echo(click.style(s, fg="green"))
        else:
            click.echo(click.style(s, fg="red"))

    ctx.obj["items"] = [items]  # For shipping as hec
