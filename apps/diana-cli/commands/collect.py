import click
from diana.apis import Orthanc
from diana.daemons import Collector

@click.command(short_help="Collect and handle studies")
@click.argument('project', type=click.STRING)
@click.argument('data_path', type=click.Path())
@click.argument('source', type=click.STRING)
@click.argument('dest', type=click.STRING)
@click.pass_context
def collect(ctx, project, data_path, source, dest):
    """Create a PROJECT key at DATA_PATH, then pull data from
    SOURCE and send to DEST."""

    services = ctx.obj.get('services')
    click.echo('Collect DICOM data')
    click.echo('------------------------')

    C = Collector()

    _source = services[source]
    source_inst = Orthanc(**_source)

    _dest = services[dest]
    dest_inst = Orthanc(**_dest)

    C.run(project, data_path, source_inst, dest_inst)


