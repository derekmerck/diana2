import click
from diana.daemons import MockSite

@click.command()
@click.argument('desc', help="Site/service/devices description")
@click.argument('dest')
@click.pass_context
def indexed_pull(ctx, desc, dest):
    """Create a mock site from DESC and send data to DEST service."""
    click.echo(index.__doc__)
    services = ctx.obj['SERVICES']

    O = None
    if dest:
        O = Orthanc(**services[dest])

    M = MockSite(pacs=O)
    M.run()
