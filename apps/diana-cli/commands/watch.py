

import click
import yaml
from diana.daemons import mk_route
from diana.utils.endpoint import Watcher

@click.command()
@click.option('-r', '--route', default=None, nargs=3)
@click.option('-R', '--routes_path', type=click.Path(exists=True), default=None)
@click.pass_context
def watch(ctx, route, routes_path):
    """
    Watch sources for events to handle based on ROUTES

    Usage:

    $ diana-cli watch -r move path:/incoming queue
    $ diana-cli watch -r move_anon queue archive
    $ diana-cli watch -r index_series archive splunk

    $ diana-cli watch -r classify_ba archive splunk

    $ diana-cli watch -r pindex_studies pacs splunk

    $ echo routes.yml
    ---
    - source: queue
      dest: archive
      handler: mv_anon
      level: instances
    - source: archive
      dest: splunk
      handler: index
      level: studies
    ...
    $ diana-cli watch -R routes.yml

    Route Handlers (Triggers):

    - say
    - mv or mv_anon
    - upload
    - index

    """

    services = ctx.obj.get('services')
    click.echo('Watcher')
    click.echo('------------------------')

    routes = []

    if route:
        r = {"handler": route[0],
             "source": route[1],
             "dest": route[1] if len(route) > 2 else None
             }

        routes.append(r)

    if routes_path:
        with open(routes_path) as f:
            _routes = yaml.load(f)
            routes = routes + _routes

    W = Watcher()

    for rt in routes:

        source_desc = services[rt['source']]
        if rt['dest']:
            dest_desc = services[rt['dest']]
        else:
            dest_desc = None

        tr = mk_route( rt['handler'],
                       source=source_desc,
                       dest=dest_desc)

        W.add_trigger(tr)

    W.run()
