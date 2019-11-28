import yaml
from datetime import datetime
from pprint import pformat
from typing import Mapping
import click
from crud.cli.utils import CLICK_ARRAY, CLICK_MAPPING, ClickEndpoint
from diana.apis import Orthanc, ProxiedDicom
from diana.utils.dicom import DicomLevel, dicom_date


@click.command(short_help="Find item in Orthanc by query for chaining")

@click.argument('source', type=ClickEndpoint(expects=Orthanc))
@click.option('--accession_numbers', '-a', type=CLICK_ARRAY,
              help="Requires PHI privileges on Montage")
# @click.option('--start_date', type=click.DateTime(),
#               default="2003-01-01",
#               help="Starting date query bound")
# @click.option('--end_date', type=click.DateTime(),
#               default=datetime.today().strftime("%Y-%m-%d"),
#               help="Ending date query bound")
@click.option('--today', is_flag=True, default=False)
@click.option('--query', '-q', "_query", type=CLICK_MAPPING,
              help="Query string")
@click.option('--level', '-l', default="studies", type=click.Choice(["studies", "series", "instances"]))
@click.option('--domain', '-d', help="Remote domain for proxied query", default=None)
@click.option('-r', '--retrieve', default=False, is_flag=True, help="Retrieve from remote for proxied query")
@click.pass_context
def ofind(ctx,
          source: Orthanc,
          accession_number: str,
          today: bool,
          query: Mapping, level,
          domain, retrieve):
    """Find studies matching yaml/json QUERY in SOURCE Orthanc or ProxiedDicom service.
     The optional proxy DOMAIN issues a remote-find to a manually proxied DICOM endpoint."""

    click.echo(click.style('Orthanc Find', underline=True, bold=True))

    source.find(query)

    if isinstance(query, str):
        query = yaml.safe_load(query)

    if accession_number:
        query["AccessionNumber"] = accession_number

    if today:
        dt = datetime.today()
        query['StudyDate'] = dicom_date(dt)

    level = DicomLevel.from_label(level)

    # For proxied Orthanc finds, we need placeholder query attribs
    if isinstance(source, ProxiedDicom) or domain:
        if level==DicomLevel.STUDIES and not query.get("NumberOfStudyRelatedInstances"):
            query["NumberOfStudyRelatedInstances"] = ""
        if level==DicomLevel.STUDIES and not query.get("ModalitiesInStudy"):
            query["ModalitiesInStudy"] = ""
        if not query.get("StudyDate") and not query.get("StudyTime"):
            query["StudyDate"] = ""
            query["StudyTime"] = ""

    if domain and hasattr(source, "rfind"):
        result = source.rfind(query, domain, level, retrieve=retrieve)
    else:
        result = source.find(query, level, retrieve=retrieve)

    ctx.obj["items"] = result

    click.echo("Found {} result{}".format(
        len(result),
        "" if len(result) == 1 else "s"
    ))
