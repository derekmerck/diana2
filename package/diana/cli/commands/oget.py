# Specialized orthanc put with anonymize and tag

import click
from crud.cli.utils import ClickEndpoint, CLICK_ARRAY, CLICK_MAPPING
from diana.apis import Orthanc

@click.command()
@click.argument("source", type=ClickEndpoint(expects=Orthanc))
@click.argument("items", type=CLICK_ARRAY, optional=True)
@click.option("-m", "--metakeys", type=CLICK_ARRAY, default=None,
              help="Meta key(s) to retrieve")
@click.option("--fkey", type=click.STRING, envvar="DIANA_FKEY",
              help="Fernet key for encrypting metadata")
@click.option("-k", "--kwargs", type=CLICK_MAPPING,
              help="""kwargs dict as yaml/json format string or @file.yaml, i.e., '{"level": "series"}'""")
@click.option("-b", "--binary", help="Get binary file as well as data", is_flag=True, default=False)
@click.pass_context
def oget(ctx, source: Orthanc, items, metakeys, fkey, kwargs, binary):
    """\
    Get studies from Orthanc.

    \b
    $ diana-cli oget oidx-xxxx... print
    $ diana-cii ofind -a 123xxx orthanc: oget orthanc: print
    """
    click.echo(click.style('Get Studies from Orthanc', underline=True, bold=True))

    if not isinstance(source, Orthanc):
        raise click.UsageError("Wrong endpoint type")

    # Compile the input items list
    if ctx.obj.get("items"):
        items.extend(ctx.obj["items"])

    # Reset the output items
    ctx.obj["items"] = []

    for item in items:
        _item = source.get(item, file=binary, **kwargs)

        if metakeys:
            for metakey in metakeys:
                metadata = source.getm(item, key=metakey)

                if fkey:
                    from diana.utils import unpack_data
                    metadata = unpack_data(metadata, fkey)

                _item.meta[metakey] = metadata

        ctx.obj["items"].append(_item)
