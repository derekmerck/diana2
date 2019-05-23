from datetime import datetime
from pprint import pformat
import click
from diana.utils.endpoint import Serializable
from diana.dixel import RadiologyReport, LungScreeningReport
# Importing all apis allows them to be immediately deserialized
from diana.apis import *

"""
$ diana-cli -S .secrets/lifespan_services.yml mfind -a 52xxxxxx -e lungrads -e radcat montage

{ ... lungrads='2', current_smoker=False, pack_years=15, radcat=(3,true) ... }

"""


@click.command(short_help="Find item in Montage by query")
@click.argument('source')
@click.option('--accession_number', '-a', help="Requires PHI privileges on Montage")
@click.option('--accessions_path',  '-A', help="Path to text file with study ids")
@click.option('--today', is_flag=True, default=False)
@click.option('--query', '-q', "_query", help="Query string", default="")
@click.option('--extraction', '-e', multiple=True,
              type=click.Choice(['radcat', 'lungrads']),
              help="Perform a data extraction on each report")
@click.pass_context
def mfind(ctx,
          source,
          accession_number,
          accessions_path,
          today,
          _query,
          extraction):
    """Find studies matching QUERY string in SOURCE Montage service."""
    services = ctx.obj.get('services')

    click.echo(click.style('Montage Find', underline=True, bold=True))

    S = Serializable.Factory.create(**services.get(source))

    query = {}

    if _query:
        query["q"] = _query

    if accession_number:
        query["q"] = accession_number

    if accessions_path:
        with open(accessions_path) as f:
            lines = f.readlines()
            accession_numbers = [line.rstrip('\n') for line in lines]
            query["q"] = " | ".join(accession_numbers)

    if today:
        dt = datetime.today()

        query["start_date"] = dt.isoformat()
        query["end_date"] = dt.isoformat()

    result = S.find(query)

    for r in result:
        if "lungrads" in extraction:
            r.meta["lungrads"] = LungScreeningReport.lungrads(r.report)
            r.meta['current_smoker'] = LungScreeningReport.current_smoker(r.report)
            r.meta["pack_years"] = LungScreeningReport.pack_years(r.report)
            r.meta["years_since_quit"] = LungScreeningReport.years_since_quit(r.report)

        if "radcat" in extraction:
            r.meta["radcat"] = RadiologyReport.radcat(r.report)

    click.echo(pformat(result))

