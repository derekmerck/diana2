import click
from pprint import pformat
from crud.cli.utils import validate_endpoint
from diana.apis import Orthanc

@click.command()
@click.argument("source", callback=validate_endpoint, type=click.STRING)
@click.argument("item", type=click.STRING)  # oid or fn
@click.argument("key", type=click.STRING)
@click.option("--fkey", type=click.STRING, envvar="DIANA_FKEY",
              help="Fernet key for decrypting metadata")

@click.pass_context
def cli(ctx, source: Orthanc, item, key, fkey):
    """Get study-level item metadata from orthanc"""
    click.echo(click.style('Orthanc Get Meta', underline=True, bold=True))
    if not isinstance(source, Orthanc):
        raise click.UsageError("Wrong endpoint type")
    meta = source.getm(item, key=key)

    if fkey:
        from diana.utils import unpack_data
        meta = unpack_data(meta, fkey)

    click.echo(pformat(meta))
