from typing import Mapping, List
import click
from crud.abc import Endpoint
from crud.cli.utils import CLICK_ENDPOINT, CLICK_MAPPING, CLICK_ARRAY


@click.command(short_help="Call endpoint method")
@click.argument('endpoint', type=CLICK_ENDPOINT)
@click.argument('method',   type=click.STRING)
@click.option('--args',    '-g', type=CLICK_ARRAY, default=[],
              help="Arguments as comma or newline separated or @file.txt format")
@click.option('--mapargs', '-m', type=CLICK_MAPPING, default={},
              help="Mapping-type arguments as json or @file.yaml format")
@click.option('--kwargs',  '-k', type=CLICK_MAPPING, default={},
              help="Keyword arguments as json or @file.yaml format")
@click.pass_context
def do(ctx, endpoint: Endpoint, method, args: List = [], mapargs: Mapping = {}, kwargs: Mapping = {}):
    """Call an arbitrary endpoint method with *args, *mapargs, and **kwargs

    \b
    $ crud-cli do redis check
    $ crud-cli do redis find -m '{"data":"test"}'
    $ crud-cli do redis get -g my_key print
    $ crud-cli do orthanc get xxxx-xxxx... -k '{"level":"series"}'
    """

    click.echo(click.style(f'Calling endpoint method: {method}', underline=True, bold=True))

    if hasattr(endpoint, method):

        if not ctx.obj.get("items"):
            ctx.obj["items"] = []

        if mapargs:
            args.append(mapargs)

        out = getattr(endpoint, method)(*args, **kwargs)
        ctx.obj["items"].append(out)

    else:
        click.echo(click.style("No such method {}".format(method), fg="red"))
        exit(1)
