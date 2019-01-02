import click
from diana.apis import DcmDir, Redis, Orthanc
from diana.daemons import FileIndexer

@click.command()
@click.argument('path')
@click.argument('registry')
@click.option('--orthanc_db', default=False, help="Use subpath width/depth=2", is_flag=True)
@click.option('--pool_size', default=10, help="Worker threads")
@click.pass_context
def findex(ctx, path, registry, orthanc_db, pool_size):
    """Inventory collections of files by accession number with a PATH REGISTRY for retrieval"""
    services = ctx.obj.get('services')
    click.echo('Register Files by Accession Number')
    click.echo('------------------------')

    file_indexer = FileIndexer(pool_size=pool_size)
    R = Redis(**services[registry])

    result = file_indexer.index_path(
        path,
        registry=R,
        recurse_style="UNSTRUCTURED" if not orthanc_db else "ORTHANC"
    )

    click.echo(result)

@click.command()
@click.argument('collection')
@click.argument('path')
@click.argument('registry')
@click.argument('dest')
@click.option('--pool_size', default=10, help="Worker threads")
@click.pass_context
def fiup(ctx, collection, path, index, dest, pool_size):
    """Pull study by COLLECTION (accession number) from a PATH REGISTRY and send to DEST"""
    services = ctx.obj.get('services')
    click.echo('Upload Registered Files by Accession Number')
    click.echo('------------------------')

    file_indexer = FileIndexer(pool_size=pool_size)
    R = Redis(**services[index])
    O = Orthanc(**services[dest])

    if collection != "ALL":

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
