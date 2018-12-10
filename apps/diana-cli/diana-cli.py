import click
import yaml
import logging
import commands


@click.group()
@click.option('--verbose/--no-verbose', default=False)
@click.option('-s', '--services', default=None)
@click.option('-S', '--services_path', type=click.Path(exists=True), default=None)
@click.pass_context
def cli(ctx, verbose, services, services_path):
    click.echo('DIANA cli')
    click.echo('Verbose mode is %s' % ('on' if verbose else 'off'))

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if services_path:
        with open(services_path) as f:
            services = yaml.load(f)
            # Runner does not instantiate ctx properly
            if not ctx.obj:
                ctx.obj = {}
            ctx.obj['services'] = services


cli.add_command(commands.check)
cli.add_command(commands.ofind)
cli.add_command(commands.index)
cli.add_command(commands.indexed_pull)


if __name__ == '__main__':
    cli(obj={})