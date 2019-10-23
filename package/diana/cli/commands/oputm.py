import click
from crud.cli.utils import validate_endpoint
from diana.apis import Orthanc

@click.command()
@click.argument("source", callback=validate_endpoint, type=click.STRING)
@click.argument("item", type=click.STRING)  # oid or fn
@click.argument("key", type=click.STRING)
@click.argument("value", type=click.STRING)
@click.pass_context
def cli(ctx, source: Orthanc, item, key, value):
    """Set study-level item metadata in orthanc"""
    click.echo(click.style('Orthanc Put Meta', underline=True, bold=True))
    if not isinstance(source, Orthanc):
        raise click.UsageError("Wrong endpoint type")
    source.putm(item, key=key, value=value)
