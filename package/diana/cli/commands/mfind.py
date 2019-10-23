from datetime import datetime
import click
from crud.cli.utils import validate_endpoint, validate_dict, validate_array

from diana.apis import Montage

"""
$ diana-cli -s @services.yml mfind -a 520xxxxx montage print

$ diana-cli -s @services.yml mfind -A @my_accessions.txt -e lungrads -e radcat montage print json > output.json

{ ... lungrads='2', current_smoker=False, pack_years=15, radcat=(3,true) ... }

"""


@click.command(short_help="Find item in montage by query for chaining")
@click.argument('source', callback=validate_endpoint, type=click.STRING)
@click.option('--accession_number', '-a', help="Requires PHI privileges on Montage")
@click.option('--accessions_list',  '-A', callback=validate_array,
              help="List of a/ns in comma or newline separated string or @file.txt format")
@click.option('--start_date', default="2003-01-01",
              help="Starting date query bound")
@click.option('--end_date', default=datetime.today().strftime("%Y-%m-%d"),
              help="Ending date query bound")
@click.option('--today', is_flag=True, default=False)
@click.option('--query', '-q', "_query", help="Query string")
@click.option('--extraction', '-e', multiple=True,
              type=click.Choice(['radcat', 'lungrads']),
              help="Perform a data extraction on each report")
@click.pass_context
def cli(ctx,
        source,
        accession_number,
        accessions_list,
        start_date,
        end_date,
        today,
        _query,
        extraction):
    """Find item in montage by query for chaining"""
    click.echo(click.style('Montage Find', underline=True, bold=True))

    from diana.dixel import RadiologyReport, LungScreeningReport

    if not isinstance(source, Montage):
        raise click.UsageError("Wrong endpoint type")

    def do_query(q):

        result = source.find(q)

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
        query["start_date"] = start_date
        query["end_date"] = end_date
        result = do_query(query)

    elif accession_number:
        query["q"] = accession_number
        result = do_query(query)

    elif accessions_list:
        result = []
        for accession_num in accessions_list:
            query["q"] = accession_num
            result.extend( do_query(query) )

    elif today:
        dt = datetime.today()
        query["start_date"] = dt.strftime("%Y-%m-%d")
        query["end_date"] = dt.strftime("%Y-%m-%d")
        result = do_query(query)

    else:
        result = []

    ctx.obj["items"] = result
