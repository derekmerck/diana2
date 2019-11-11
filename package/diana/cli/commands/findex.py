from hashlib import sha1
import click
from crud.endpoints import Redis
from diana.apis import DcmDir
from crud.cli.utils import ClickEndpoint, CLICK_ARRAY


@click.command(short_help="Index files by accession number")
@click.argument("source", type=ClickEndpoint(expects=DcmDir))
@click.argument("index", type=ClickEndpoint(expects=Redis))
@click.pass_context
def findex(ctx, source: DcmDir, index: Redis):
    """Index files by accession number

    \b
    $ diana-cli findex path:/data redis:
    """
    click.echo(click.style('Index files by accession number', underline=True, bold=True))

    index.prefix = sha1(source.path).hexdigest()[0:7]

    for f in source.files():
        d = source.get(f)
        collection_id = d.tags.get("AccessionNumber")
        index.sput(d, collection_id)


@click.command(name="findex-get")
@click.argument("source", type=ClickEndpoint(expects=DcmDir))
@click.argument("index", type=ClickEndpoint(expects=Redis))
@click.argument("collection_ids", type=CLICK_ARRAY)
@click.option("-b", "--binary", help="Get binary file as well as data", is_flag=True, default=False)
@click.pass_context
def findex_get(ctx, source: DcmDir, index: Redis, collection_ids):
    """Put indexed files in a destination node by accession number

    \b
    $ diana-cli findex-get path:/data redis: all print
    $ diana-cli findex-get -b path:/data redis: CT3456789 oput orthanc:
    """
    click.echo(click.style('Put indexed files by accession number', underline=True, bold=True))

    index.prefix = sha1(source.path).hexdigest()[0:7]

    if "ALL" in collection_ids or "all" in collection_ids:
        collection_ids = index.keys()

    for collection_id in collection_ids:
        items = index.sget(collection_id)

        for item in items:
            d = source.get(item, file=True)
            ctx.obj["items"].append(d)
