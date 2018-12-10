import yaml
import click
from diana.apis import Orthanc
from diana.utils.dicom import DicomLevel

@click.command()
@click.argument('query')
@click.argument('source')
@click.option('--domain', help="Domain for proxied query", default=None)
@click.option('-r', '--retrieve', default=False, is_flag=True)
@click.pass_context
def ofind(ctx, query, source, domain, retrieve):
    """Find studies matching yaml/json QUERY in SOURCE Orthanc service {optionally with proxy DOMAIN}"""
    click.echo(ofind.__doc__)
    services = ctx.obj['SERVICES']

    S = Orthanc(**services.get(source))
    if isinstance(query, str):
        query = yaml.safe_load(query)

    if domain:
        result = S.rfind(query, domain, DicomLevel.STUDIES, retrieve=retrieve)

    else:
        result = S.find(query, DicomLevel.STUDIES)

    click.echo(result)
