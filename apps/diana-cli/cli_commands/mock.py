import click
import yaml
from diana.apis import Orthanc
from diana.daemons import MockSite
from diana.daemons.mock_site import sample_site_desc

epilog = """
DESC must be a mock-site description in yaml format.

\b
---
- name: Example Hospital
  services:
  - name: Main CT
    modality: CT
    devices: 3
    studies_per_hour: 15
  - name: Main MR
    modality: MR
    devices: 2
    studies_per_hour: 4
...
"""

@click.command(epilog=epilog, short_help="Generate mock DICOM traffic")
@click.argument('desc', required=False)
@click.option('--dest', help="Destination DICOM service")
@click.pass_context
def mock(ctx, desc, dest):
    """Generate synthetic studies on a schedule according to a site
    description DESC.  Studies are optionally forwarded to an endpoint DEST."""

    services = ctx.obj.get('services')
    click.echo('Generate mock DICOM data')
    click.echo('------------------------')

    if not desc:
        desc = sample_site_desc
    desc = yaml.load(desc)

    H = MockSite.Factory.create(desc=desc)

    O = None
    if dest:
        _desc = services[dest]
        O = Orthanc(**_desc)

    for h in H:
        h.run(pacs=O)
