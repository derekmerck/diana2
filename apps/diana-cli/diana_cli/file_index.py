import click
from diana.apis import DcmDir, Redis, Orthanc
from diana.daemons import FileIndexer


@click.command(short_help="Create a persistent DICOM file index")
@click.argument('path')
@click.argument('registry')
@click.option('-o', '--orthanc_db', default=False,   help="Use subpath width/depth=2", is_flag=True)
@click.option('-r', '--regex',      default="*.dcm", help="Glob regular expression")
@click.option('-p', '--pool_size',  default=10,      help="Worker threads")
@click.pass_context
def findex(ctx, path, registry, orthanc_db, regex, pool_size):
    """Inventory collections of files by accession number with a PATH REGISTRY for retrieval"""
    services = ctx.obj.get('services')

    click.echo(click.style('Register Files by Accession Number', underline=True, bold=True))

    file_indexer = FileIndexer(pool_size=pool_size)
    R = Redis(**services[registry])

    result = file_indexer.index_path(
        path,
        registry=R,
        rex=regex,
        recurse_style="UNSTRUCTURED" if not orthanc_db else "ORTHANC"
    )

    click.echo(result)


@click.command(short_help="Upload indexed DICOM files")
@click.argument('collection')
@click.argument('path')
@click.argument('registry')
@click.argument('dest')
@click.option('-p', '--pool_size', default=10, help="Worker threads")
@click.option('-d', '--dryrun', default=False, is_flag=True)
@click.pass_context
def fiup(ctx, collection, path, registry, dest, pool_size, dryrun):
    """Collect files in a study by COLLECTION (accession number) using a
    PATH REGISTRY, and send to DEST."""
    services = ctx.obj.get('services')

    click.echo(click.style('Upload Registered Files by Accession Number',
                           underline=True, bold=True))

    file_indexer = FileIndexer(pool_size=pool_size)
    R = Redis(**services[registry])
    O = Orthanc(**services[dest])

    if collection != "ALL":

        items = file_indexer.items_on_path(path)
        click.echo('Expecting {} items on path'.format(len(items)))

        if dryrun:
            exit()

        result = file_indexer.upload_collection(
            collection=collection,
            basepath=path,
            registry=R,
            dest=O
        )

    else:
        result = file_indexer.upload_path(
            basepath=path,
            registry=R,
            dest=O
        )

    click.echo(result)
