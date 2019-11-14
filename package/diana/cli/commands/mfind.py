from datetime import datetime
import logging
from pprint import pformat
import click
from crud.cli.utils import ClickEndpoint, CLICK_ARRAY, CLICK_MAPPING
from diana.apis import Montage
from diana.dixel import RadiologyReport, LungScreeningReport


@click.command(short_help="Find items in Montage by query for chaining")
@click.argument('source', type=ClickEndpoint(expects=Montage))
@click.option('--accession_numbers', '-a', type=CLICK_ARRAY,
              help="Requires PHI privileges on Montage")
@click.option('--start_date', type=click.DateTime(),
              default="2003-01-01",
              help="Starting date query bound")
@click.option('--end_date', type=click.DateTime(),
              default=datetime.today().strftime("%Y-%m-%d"),
              help="Ending date query bound")
@click.option('--today', is_flag=True, default=False)
@click.option('--query', '-q', "_query", type=CLICK_MAPPING,
              help="Query string")
@click.option('--extraction', '-e', multiple=True,
              type=click.Choice(['radcat', 'lungrads']),
              help="Perform a data extraction on each report")
@click.pass_context
def mfind(ctx,
          source: Montage,
          accession_numbers,
          start_date,
          end_date,
          today,
          _query,
          extraction):
    """Find items in Montage by query for chaining.

    \b
    $ diana-cli mfind -a 520xxxxx montage print
    { "AccesssionNumber": 520xxxxx, "PatientID": abcdef, ... }

    $ diana-cli mfind -a @my_accessions.txt -e lungrads -e radcat montage print jsonl > output.jsonl
    $ cat output.jsonl
    { ... lungrads='2', current_smoker=False, pack_years=15, radcat=(3,true) ... }
    """

    click.echo(click.style('Montage Find', underline=True, bold=True))

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

    elif accession_numbers:
        result = []
        for accession_number in accession_numbers:
            click.echo(f"Looking up accession number: {accession_number}")
            query["q"] = accession_number
            result.extend( do_query(query) )

    elif today:
        dt = datetime.today()
        query["start_date"] = dt.strftime("%Y-%m-%d")
        query["end_date"] = dt.strftime("%Y-%m-%d")

        logging.debug(pformat(query))
        result = do_query(query)

    else:
        result = []

    ctx.obj["items"] = result

    click.echo("Found {} result{}".format(
        len(result),
        "" if len(result) == 1 else "s"
    ))
