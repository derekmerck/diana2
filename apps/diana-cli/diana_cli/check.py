import logging
from pprint import pformat
from collections import Mapping
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

    for k, v in services.items():
        if endpoints and k not in endpoints:
            logging.debug("{} not in list".format(k))
            continue
        if not isinstance(v, Mapping):
            logging.debug("{} not mapping".format(v))
            continue
        ep = Serializable.Factory.create(**v)
        try:
            ready = ep.check()
            out = click.style("{}: {}".format(k, "Ready" if ready else "Not Ready"),
                              fg="green" if ready else "red")
        except NotImplementedError:
            out = click.style("{}: {}".format(k, "Unimplemented health check"),
                              fg="yellow")
        click.echo(out)



@click.command(short_help="Get endpoint info")
@click.argument('endpoints', nargs=-1)
@click.pass_context
def info(ctx, endpoints):
    """Survey status of service ENDPOINTS"""
    services = ctx.obj.get('services')

    click.echo(click.style('Services', underline=True, bold=True))
    click.echo(pformat(services))
    click.echo()

    click.echo(click.style('Checking endpoint info', underline=True, bold=True))

    for k, v in services.items():
        if endpoints and k not in endpoints:
            logging.debug("{} not in list".format(k))
            continue
        if not isinstance(v, Mapping):
            logging.debug("{} not mapping".format(v))
            continue
        ep = Serializable.Factory.create(**v)
        try:
            info = ep.info()
            out = click.style("{}: {}".format(k, "Ready" if info else "Not Ready"),
                              fg="green" if info else "red")
            if info:
                click.echo(pformat(info))
        except NotImplementedError:
            out = click.style("{}: {}".format(k, "Unimplemented info"),
                              fg="yellow")
        click.echo(out)


