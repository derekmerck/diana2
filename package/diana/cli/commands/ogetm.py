import click
from pprint import pformat
from crud.cli.utils import ClickEndpoint
from diana.apis import Orthanc

@click.command()
@click.argument("source", type=ClickEndpoint(expects=Orthanc))
@click.argument("item", type=click.STRING)  # oid or fn
@click.argument("key", type=click.STRING)
@click.option("--fkey", type=click.STRING, envvar="DIANA_FKEY",
              help="Fernet key for decrypting metadata")

@click.pass_context
def ogetm(ctx, source: Orthanc, item, key, fkey):
    """Get study-level item metadata from Orthanc"""
    click.echo(click.style('Orthanc Get Meta', underline=True, bold=True))
    if not isinstance(source, Orthanc):
        raise click.UsageError("Wrong endpoint type")
    meta = source.getm(item, key=key)

    if fkey:
        from diana.utils import unpack_data
        meta = unpack_data(meta, fkey)

    click.echo(pformat(meta))
