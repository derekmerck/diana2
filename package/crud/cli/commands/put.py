import click
from crud.cli.utils import CLICK_ENDPOINT, CLICK_MAPPING


@click.command(short_help="Put chained items in endpoint")
@click.argument("dest", type=CLICK_ENDPOINT)
@click.option("-k", "--kwargs", type=CLICK_MAPPING,
              help="""kwargs dict as yaml/json format string or @file.yaml, i.e., '{"level": "series"}'""")
@click.pass_context
def put(ctx, dest, kwargs):
    """Put chained items in endpoint"""
    click.echo(click.style('Putting Items in Dest', underline=True, bold=True))
    for item in ctx.obj.get("items", []):
        dest.put(item, **kwargs)
