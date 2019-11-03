import click
from crud.cli.utils import ClickEndpoint, CLICK_MAPPING
from diana.apis import Orthanc

@click.command()
@click.argument("source",  type=ClickEndpoint(expects=Orthanc))
@click.argument("item",    type=click.STRING)  # oid or fn
@click.argument("updates", type=CLICK_MAPPING)
@click.pass_context
def oputm(ctx, source: Orthanc, item, key, value):
    """Set study-level item metadata in Orthanc"""
    click.echo(click.style('Orthanc Put Meta', underline=True, bold=True))
    source.putm(item, key=key, value=value)
