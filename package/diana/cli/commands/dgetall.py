import os
import click
from crud.cli.utils import ClickEndpoint
from diana.apis import DcmDir


@click.command()
@click.argument("source", type=ClickEndpoint(expects=DcmDir))
@click.option("-b", "--binary", help="Get binary file as well as data", is_flag=True, default=False)
@click.pass_context
def dgetall(ctx, source: DcmDir, binary):
    """Get all instances from DcmDir for chaining"""
    click.echo(click.style('Get All Items from DcmDir', underline=True, bold=True))

    items = []
    for root, dirs, files in os.walk(source.path):
        for file in files:
            items.append(os.path.join(root, file))

    for item in items:
        _item = source.get(item, file=binary)
        if _item:
            ctx.obj["items"].append(_item)

    ctx.obj["source"] = source
