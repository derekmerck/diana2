import click
import yaml
from diana.apis import Orthanc
from diana.daemons import MockSite
from diana.daemons.mock_site import sample_site_desc

@click.command()
@click.argument('desc', required=False)
@click.option('--dest', help="Destination service")
@click.pass_context
def mock(ctx, desc, dest):
    """Create a mock site from DESC and send data to DEST service."""
    services = ctx.obj.get('services')
    click.echo('Generate mock DICOM data')
    click.echo('------------------------')

    if not desc:
        desc = sample_site_desc
    desc = yaml.load(desc)

    H = MockSite.Factory.create(desc=desc)

    O = None
    if dest:
        O = Orthanc(**services[dest])

    for h in H:
        h.run(pacs=O)
