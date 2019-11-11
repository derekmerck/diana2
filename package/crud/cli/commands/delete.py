import click
from crud.cli.utils import CLICK_ENDPOINT, CLICK_MAPPING, CLICK_ARRAY


@click.command(short_help="Delete items in endpoint")
@click.argument("source", type=CLICK_ENDPOINT)
@click.argument("items", type=CLICK_ARRAY, required=False)
@click.pass_context
def delete(ctx, source, items):
    """Remove items from endpoint"""
    click.echo(click.style('Removing Items in Source', underline=True, bold=True))

    items.extend( ctx.obj.get("items", []) )

    for item in items:
        source.delete(item)
