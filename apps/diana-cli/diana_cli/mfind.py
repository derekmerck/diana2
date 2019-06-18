from datetime import datetime
from pprint import pformat
import json
import click
from diana.utils.endpoint import Serializable
from diana.utils import SmartJSONEncoder
from diana.dixel import RadiologyReport, LungScreeningReport
# Importing all apis allows them to be immediately deserialized
from diana.apis import *

"""
$ diana-cli -S .secrets/lifespan_services.yml mfind -A studies.txt -j montage

$ diana-cli -S .secrets/lifespan_services.yml mfind -a 52xxxxxx -e lungrads -e radcat montage

{ ... lungrads='2', current_smoker=False, pack_years=15, radcat=(3,true) ... }

"""


@click.command(short_help="Find item in Montage by query")
@click.argument('source')
@click.option('--accession_number', '-a', help="Link multiple a/ns with ' | ', requires PHI privileges on Montage")
@click.option('--accessions_path',  '-A', help="Path to text file with study ids")
@click.option('--today', is_flag=True, default=False)
@click.option('--query', '-q', "_query", help="Query string", default="")
@click.option('--extraction', '-e', multiple=True,
              type=click.Choice(['radcat', 'lungrads']),
              help="Perform a data extraction on each report")
@click.option('--json', '-j', "as_json", is_flag=True, default=False, help="Output as json")
@click.pass_context
def mfind(ctx,
          source,
          accession_number,
          accessions_path,
          today,
          _query,
          extraction,
          as_json):
    """Find studies matching QUERY string in SOURCE Montage service."""
    services = ctx.obj.get('services')

    click.echo(click.style('Montage Find', underline=True, bold=True))

    S = Serializable.Factory.create(**services.get(source))


    def do_query(q):

        result = S.find(q)

        for r in result:
            if "lungrads" in extraction:
                r.meta["lungrads"] = LungScreeningReport.lungrads(r.report)
                r.meta['current_smoker'] = LungScreeningReport.current_smoker(r.report)
                r.meta["pack_years"] = LungScreeningReport.pack_years(r.report)
                r.meta["years_since_quit"] = LungScreeningReport.years_since_quit(r.report)

            if "radcat" in extraction:
                r.meta["radcat"] = RadiologyReport.radcat(r.report)

        return result


    query = {}

    if _query:
        query["q"] = _query
        result = do_query(query)

    elif accession_number:
        query["q"] = accession_number
        result = do_query(query)

    elif accessions_path:
        with open(accessions_path) as f:
            lines = f.readlines()
            accession_numbers = [line.rstrip('\n') for line in lines]
            result = set()
            for accession_num in accession_numbers:
                query["q"] = accession_num
                result.update( do_query(query) )

    elif today:
        dt = datetime.today()

        query["start_date"] = dt.isoformat()
        query["end_date"] = dt.isoformat()
        result = do_query(query)

    else:
        result = []

    if as_json:
        result = json.dumps([d.asdict() for d in result], cls=SmartJSONEncoder, sort_keys=True,
                            indent=4, separators=(',', ': '))

    else:
        result = pformat(result)

    click.echo(result)

