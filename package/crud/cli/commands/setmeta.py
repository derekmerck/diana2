import click
from crud.cli.utils import CLICK_MAPPING


@click.command()
@click.argument("update_dict", type=CLICK_MAPPING)
@click.pass_context
def setmeta(ctx, update_dict):
    """Set metadata kvs for chained items"""
    click.echo(click.style('Set metadata key value pairs', underline=True, bold=True))

    for item in ctx.obj.get("items"):
        item.meta.update(update_dict)
