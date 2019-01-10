from pathlib import Path
import click
from diana.apis import Orthanc, DcmDir
from diana.daemons import Collector

"""

$ python3 diana-cli.py --verbose -S ../../.secrets/lifespan_services.yml collect all_cr /Users/derek/data/DICOM/all_cr bridge pacs

$ python3 diana-cli.py --verbose -S ../../.secrets/lifespan_services.yml collect mam_mr+bx /Users/derek/data/DICOM/mam_mr+bx bridge pacs review01

"""

@click.command(short_help="Collect and handle studies")
@click.argument('project', type=click.STRING)
@click.argument('data_path', type=click.Path())
@click.argument('source', type=click.STRING)
@click.argument('domain', type=click.STRING)
@click.argument('dest', type=click.STRING, required=False, default=None)
@click.pass_context
def collect(ctx, project, data_path, source, domain, dest):
    """Create a PROJECT key at DATA_PATH, then pull data from
    SOURCE and send to DEST."""

    services = ctx.obj.get('services')
    click.echo('Collect DICOM data')
    click.echo('------------------------')

    C = Collector()

    _source = services[source]
    source_inst = Orthanc(**_source)

    if not dest:
        path = data_path / Path("data")
        dest_inst = DcmDir(path=path, subpath_width=2, subpath_depth=2)
    elif dest.startswith("path:"):
        path = dest.split(":")[-1]
        dest_inst = DcmDir(path=path, subpath_width=2, subpath_depth=2)
    else:
        _dest = services[dest]
        dest_inst = Orthanc(**_dest)

    C.run(project, data_path, source_inst, domain, dest_inst)


