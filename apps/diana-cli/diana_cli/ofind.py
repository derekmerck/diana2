import yaml
from datetime import datetime
from pprint import pformat
import click
from diana.utils.endpoint import Serializable
from diana.utils.dicom import DicomLevel, dicom_date
# importing all apis allows them to be immediately deserialized
from diana.apis import *

@click.command(short_help="Find item by query")
@click.argument('source')
@click.option('--accession_number', '-a')
@click.option('--today', is_flag=True, default=False)
@click.option('--query', '-q', help="Query in json format", default="{}")
@click.option('--domain', '-d', help="Domain for proxied query when using Orthanc source", default=None)
@click.option('-r', '--retrieve', default=False, is_flag=True)
@click.pass_context
def ofind(ctx,
          source,
          accession_number,
          today,
          query,
          domain, retrieve):
    """Find studies matching yaml/json QUERY in SOURCE Orthanc or ProxiedDicom service.
     The optional proxy DOMAIN issues a remote-find to a manually proxied DICOM endpoint."""
    services = ctx.obj.get('services')

    click.echo(click.style('Orthanc Find', underline=True, bold=True))

    S = Serializable.Factory.create(**services.get(source))

    # S = Orthanc(**services.get(source))
    if isinstance(query, str):
        query = yaml.safe_load(query)

    if accession_number:
        query["AccessionNumber"] = accession_number

    if today:
        dt = datetime.today()
        query['StudyDate'] = dicom_date(dt)

    if domain and hasattr(S, "rfind"):
        result = S.rfind(query, domain, DicomLevel.STUDIES, retrieve=retrieve)
    else:
        result = S.find(query, DicomLevel.STUDIES, retrieve=retrieve)

    click.echo(pformat(result))
