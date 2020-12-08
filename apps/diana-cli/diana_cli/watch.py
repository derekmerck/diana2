import click
import yaml
from diana.daemons import mk_route
from diana.utils.endpoint import Watcher

epilog="""
Examples:

\b
$ diana-cli watch -r upload_files path:/incoming queue
$ diana-cli watch -r anon_and_send_instances queue archive
$ diana-cli watch -r index_studies pacs splunk
$ diana-cli watch -r classify_ba archive splunk
$ diana-cli watch -R routes.yml

Multiple ROUTES file format:

\b
---
- handler: upload_files
  source: "path:/incoming"
  dest: queue
- handler: anon_and_send_instances
  source: queue
  dest: archive
- handler: index_studies
  source: pacs
  dest: splunk
...

Provided route handlers:

\b
- say_dlvl
- send_dlvl or anon_and_send_dlvl
- upload_files
- index_dlvl
"""


@click.command(short_help="Watch sources and route events", epilog=epilog)
@click.option('-r', '--route', default=None, nargs=3)
@click.option('-R', '--routes_path', type=click.Path(exists=True), default=None)
@click.pass_context
def watch(ctx, route, routes_path):
    """Watch sources for events to handle based on ROUTES"""
    services = ctx.obj.get('services')

    click.echo(click.style('Watcher', underline=True, bold=True))

    routes = []

    if route:
        r = {
             "handler": route[0],
             "source": route[1],
             "dest": route[2]
            }

        routes.append(r)

    if routes_path:
        with open(routes_path) as f:
            _routes = yaml.load(f)
            routes = routes + _routes

    W = Watcher()

    for rt in routes:

        if rt["source"].startswith("path:"):
            source_desc = {
                "ctype": "ObservableDcmDir",
                "path": r["source"][5:]
            }
        else:
            source_desc = services[rt['source']]

        if services.get( rt['dest'] ):
            dest_desc = services[rt['dest']]
        else:
            dest_desc = None

        tr = mk_route( rt['handler'],
                       source_desc=source_desc,
                       dest_desc=dest_desc)

        W.add_trigger(tr)

    W.run()
