from pathlib import Path
import click
from diana.apis import Orthanc, DcmDir
from diana.daemons import Collector

"""

$ python3 diana-cli.py --verbose -S ../../.secrets/lifespan_services.yml collect -b 2 all_cr /Users/derek/data/DICOM/all_cr bridge pacs

$ python3 diana-cli.py --verbose -S ../../.secrets/lifespan_services.yml collect mam_mr+bx /Users/derek/data/DICOM/mam_mr+bx bridge pacs review01

"""


@click.command(short_help="Collect and handle studies")
@click.argument('project', type=click.STRING)
@click.argument('data_path', type=click.Path())
@click.argument('source', type=click.STRING)
@click.argument('domain', type=click.STRING)
@click.argument('dest', type=click.STRING, required=False, default=None)
@click.option('-a', '--anonymize', is_flag=True,
                default=False)
@click.option('-b', '--subpath_depth', type=int, default=0, help="Number of sub-directories to use  (if dest is directory)")
@click.pass_context
def collect(ctx, project, data_path, source, domain, dest, anonymize, subpath_depth):
    """Create a PROJECT key at DATA_PATH, then pull data from
    SOURCE and send to DEST."""
    services = ctx.obj.get('services')

    click.echo(click.style('Collect DICOM data', underline=True, bold=True))

    C = Collector()

    _source = services[source]
    source_inst = Orthanc(**_source)

    if not dest:
        path = data_path / Path("data")
        dest_inst = DcmDir(path=path, subpath_width=2, subpath_depth=subpath_depth)
    elif dest.startswith("path:"):
        path = dest.split(":")[-1]
        dest_inst = DcmDir(path=path, subpath_width=2, subpath_depth=subpath_depth)
    else:
        _dest = services[dest]
        dest_inst = Orthanc(**_dest)

    C.run(project, data_path, source_inst, domain, dest_inst, anonymize)
