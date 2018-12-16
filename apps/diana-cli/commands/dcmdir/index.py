
import click
from diana.apis import DcmDir, Redis, Orthanc

@click.command()
@click.argument('path')
@click.argument('index')
@click.option('--orthanc_db', default=False, help="Use subpath width/depth = 2", is_flag=True)
@click.pass_context
def index(ctx, path, index, orthanc_db):
    """Inventory dicom dir PATH with INDEX service for retrieval"""
    click.echo(index.__doc__)
    services = ctx.obj.get('services')
    click.echo('Index by Accession Number')
    click.echo('------------------------')

    spw = 0
    spd = 0
    if orthanc_db:
        spw = 2
        spd = 2

    D = DcmDir(path=path, subpath_width=spw, subpath_depth=spd)
    R = Redis(**services[index])

    result = D.index_to(R)
    click.echo(result)

@click.command()
@click.argument('accession_number')
@click.argument('path')
@click.argument('index')
@click.argument('dest')
@click.option('--orthanc_db', default=False, help="Use subpath width/depth = 2", is_flag=True)
@click.pass_context
def indexed_pull(ctx, accession_number, path, index, dest, orthanc_db):
    """Pull study by accession number from a PATH with INDEX service and send to DEST"""
    click.echo(indexed_pull.__doc__)
    services = ctx.obj.get('services')
    click.echo('Pull Indexed by Accession Number')
    click.echo('------------------------')

    spw = 0
    spd = 0
    if orthanc_db:
        spw = 2
        spd = 2

    D = DcmDir(path=path, subpath_width=spw, subpath_depth=spd)
    R = Redis(**services[index])
    O = Orthanc(**services[dest])

    worklist = D.get_indexed_study(accession_number, R)
    for item in worklist:
        d = D.get(item, get_file=True)
        O.put(d)
