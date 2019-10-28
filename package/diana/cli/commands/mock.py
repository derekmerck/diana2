import click
import yaml
from crud.cli.utils import CLICK_MAPPING, ClickEndpoint
from diana.apis import Orthanc
from diana.daemons import MockSite
from diana.daemons.mock_site import sample_site_desc

epilog = f"""
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
@click.argument('desc', required=False, type=CLICK_MAPPING)
@click.option('--dest', type=ClickEndpoint(expects=Orthanc),
              help="Destination DICOM service")
@click.pass_context
def mock(ctx, desc, dest: Orthanc):
    """Generate synthetic studies on a schedule according to a site
    description DESC.  Studies are optionally forwarded to an endpoint DEST."""

    click.echo(click.style('Generate mock DICOM data', underline=True, bold=True))

    if not desc:
        desc = sample_site_desc
    desc = yaml.load(desc)

    H = MockSite.Factory.create(desc=desc)

    for h in H:
        if dest:
            h.run(pacs=dest)
        else:
            h.run()
