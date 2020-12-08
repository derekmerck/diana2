import click
from crud.abc import Watcher, Trigger
from crud.cli.utils import CLICK_MAPPING, CLICK_ENDPOINT
from diana.daemons import mk_route

# TODO: Fix watcher ...

epilog="""
Examples:
\b
$ diana-cli watch upload_files path:/incoming queue
$ diana-cli watch anon_and_send_instances queue archive
$ diana-cli watch index_studies pacs splunk
$ diana-cli watch classify_ba archive splunk
$ diana-cli watch -r @routes.yml
Multiple ROUTES file format:
\b
---
- source: orthanc
  event_type: new_study
  actions:
    - say

- source: path:/incoming
  dest: orthanc
  event_type: new_file
  action:
    - source.get
    - dest.put
    - dest.anonymize
    - dest.delete
- source: orthanc
  dest: splunk
  event_type: new_study
  action:
    - put
...
Provided route handlers:
\b
- say_dlvl
- send_dlvl or anon_and_send_dlvl
- upload_files or upload_and_anon_files
- index_dlvl
"""


@click.command(short_help="Watch sources and route events", epilog=epilog)
@click.option("--routes", "-r", type=CLICK_MAPPING, default=None)
@click.option("--handler", "-h", type=click.STRING, default=None)
@click.option("--source", "-s", type=CLICK_ENDPOINT, default=None)
@click.option("--dest", "-d",   type=CLICK_ENDPOINT, default=None)
@click.pass_context
def watch(ctx, routes, handler, source, dest):
    """Watch sources for events to handle based on ROUTES"""
    services = ctx.obj.get('services')

    click.echo(click.style('Watcher', underline=True, bold=True))

    W = Watcher()

    source  = services.get(source)
    dest    = services.get(dest)
    handler = mk_route(handler, source=source, dest=dest)

    tr = Trigger(source=source,
                 dest=dest,
                 handler=handler)

    W.add_trigger(tr)

    W.run()
