from pprint import pformat
import click


@click.command(name="print")
@click.argument("_format", type=click.Choice(['plain', 'jsonl', 'csv']), default="plain")
@click.pass_context
def _print(ctx, _format):
    """Print chained items to stdout"""
    click.echo(click.style('Printing Items', underline=True, bold=True))
    for item in ctx.obj.get("items", []):

        if not hasattr(item, "asdict") and not hasattr(item, "json"):
        # if not isinstance(item, Serializable):
            s = item
            # raise TypeError("Can not dump non-serializable item-type")

        elif _format=="plain":
            s = pformat(item.asdict())

        elif _format=="jsonl":
            s = item.json()

        else:
            raise(NotImplementedError)
        click.echo(s)
