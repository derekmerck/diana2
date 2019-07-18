import yaml
from datetime import datetime
from pprint import pformat
import click
from crud.abc import Serializable
from diana.utils.dicom import DicomLevel, dicom_date
# importing all apis allows them to be immediately deserialized
from diana.apis import *


@click.command(short_help="Find item in Orthanc by query")
@click.argument('source')
@click.option('--accession_number', '-a')
@click.option('--today', is_flag=True, default=False)
@click.option('--query', '-q', help="Query in json format", default="{}")
@click.option('--level', '-l', default="studies")
@click.option('--domain', '-d', help="Domain for proxied query when using Orthanc source", default=None)
@click.option('-r', '--retrieve', default=False, is_flag=True)
@click.pass_context
def ofind(ctx,
          source,
          accession_number,
          today,
          query, level,
          domain, retrieve):
    """Find studies matching yaml/json QUERY in SOURCE Orthanc or ProxiedDicom service.
     The optional proxy DOMAIN issues a remote-find to a manually proxied DICOM endpoint.

     $ diana-cli ofind -q "{'StudyDescription': ''}" -d radarch sticky_bridge
     """
    services = ctx.obj.get('services')

    click.echo(click.style('Orthanc Find', underline=True, bold=True))

    level = DicomLevel.from_label(level)
    S = Serializable.Factory.create(**services.get(source))

    # S = Orthanc(**services.get(source))
    if isinstance(query, str):
        query = yaml.safe_load(query)

    if accession_number:
        query["AccessionNumber"] = accession_number

    if today:
        dt = datetime.today()
        query['StudyDate'] = dicom_date(dt)

    # # For simple local Orthanc find, we don't need placeholder query attribs
    # if not isinstance(S, Orthanc) and not domain:
    #     if level==DicomLevel.STUDIES and not query.get("NumberOfStudyRelatedInstances"):
    #         query["NumberOfStudyRelatedInstances"] = ""
    #     if level==DicomLevel.STUDIES and not query.get("ModalitiesInStudy"):
    #         query["ModalitiesInStudy"] = ""
    #     if not query.get("StudyDate") and not query.get("StudyTime"):
    #         query["StudyDate"] = ""
    #         query["StudyTime"] = ""

    if domain and hasattr(S, "rfind"):
        result = S.rfind(query, domain, level, retrieve=retrieve)
    else:
        result = S.find(query, level, retrieve=retrieve)

    click.echo(pformat(result))
