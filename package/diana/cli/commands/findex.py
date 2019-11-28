"""

Simplest
------------

`$ diana-cli dgetall -b path:/ericsfiles oput -a ericsorthanc`

`dgetall` reads all DICOM files on a path, the `-b` flag tells it to also read the binary file.

`oput` sends any previously found DICOM items to an Orthanc instance, the `-a` flag tells it to anonymize them on receipt.

Advanced
------------

`$ diana-cli dgetall path:/ericsfiles findex my_redis`

In this case, the items loaded by `dgetall` do not include the binary.

`findex` uses a Redis instance to organize collections of loose files into studies by accession number, so that you can upload them or otherwise manipulate them one-by-one or repeatedly without rereading the entire folder.

Once the index is created, you can upload the files by a/n (or "all")

```
$ diana-cli findex-get path:/ericsfiles my_redis my_accession_num print
... prints tags in each file ...
```

`$ diana-cli findex-get -b path:/ericsfiles my_redis all oput -a ericsorthanc`

Note in this case, the file for each item has to be loaded by findex-get, b/c Redis doesn't store any binary info and Orthanc ingests files.

This is a super useful feature for pulling data from the massive archive of loose files on the old CIRR, where just reading the all the files to figure out what is actually in there takes about a week, but then sending items one-by-one to Orthanc for Scott can be very useful.  But I still need to implement a couple more features to really work well for that.


"""


from hashlib import sha1
from pprint import pformat
import click
from crud.endpoints import Redis
from diana.apis import DcmDir
from crud.cli.utils import ClickEndpoint, CLICK_ARRAY


@click.command(short_help="Index items by accession number")
# @click.argument("source", type=ClickEndpoint(expects=DcmDir))
@click.argument("index", type=ClickEndpoint(expects=Redis))
@click.pass_context
def findex(ctx, index: Redis):
    """Index chained files by accession number

    \b
    $ diana-cli findex path:/data redis:
    """
    click.echo(click.style('Index files by accession number', underline=True, bold=True))
    index.prefix = sha1(ctx.obj.get("source").path.encode('utf8')).hexdigest()[0:7]

    for item in ctx.obj.get("items"):
        collection_id = item.tags.get("AccessionNumber")
        index.sput(item, collection_id)


@click.command(name="findex-get")
@click.argument("source", type=ClickEndpoint(expects=DcmDir))
@click.argument("index", type=ClickEndpoint(expects=Redis))
@click.argument("collection_ids", type=CLICK_ARRAY)
@click.option("-b", "--binary", help="Get binary file as well as data", is_flag=True, default=False)
@click.pass_context
def findex_get(ctx, source: DcmDir, index: Redis, collection_ids, binary):
    """Put indexed files in a destination node by accession number

    \b
    $ diana-cli findex-get path:/data redis: all print
    $ diana-cli findex-get -b path:/data redis: CT3456789 oput orthanc:
    """
    click.echo(click.style('Put indexed files by accession number', underline=True, bold=True))

    index.prefix = sha1(source.path.encode('utf8')).hexdigest()[0:7]

    if "ALL" in collection_ids or "all" in collection_ids:
        collection_ids = index.skeys()
        click.echo("Collection IDs")
        click.echo(pformat(collection_ids))

    for collection_id in collection_ids:
        items = index.sget(collection_id)

        click.echo("Collection Items")
        click.echo(items)

        for item in items:
            if binary:
                # Refresh entire object
                item = source.get(item, file=True)
            ctx.obj["items"].append(item)
