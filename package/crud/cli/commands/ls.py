import click


@click.command(short_help="List all services and health")
@click.option("--health-check/--skip-health-check", "-h/-k", default=True, help="Skip health")
@click.pass_context
def ls(ctx, health_check):
    """List all services and health

    \b
    $ crud-cli ls
    """
    click.echo(click.style('List Services and Health', underline=True, bold=True))

    for ep in ctx.obj["services"].get_all():
        if health_check:
            avail = ep.check()
        else:
            avail = "Unknown"

        s = "{}: {}".format(ep.name, "Ready" if avail else "Unavailable")
        if avail:
            click.echo(click.style(s, fg="green"))
        else:
            click.echo(click.style(s, fg="red"))
