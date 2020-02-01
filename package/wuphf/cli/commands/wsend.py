import click
from pprint import pformat
from crud.cli.utils import ClickEndpoint, CLICK_MAPPING
from wuphf.abc import Messenger


@click.command(short_help="Send items via Messenger endpoint")
@click.argument('messenger', type=ClickEndpoint(expects=Messenger))
@click.option('--data', type=CLICK_MAPPING)
@click.option('--target', '-t', type=click.STRING,
              help="Optional target, if not using a dedicated messenger")
@click.option('--msg_t', '-m', type=click.STRING,
              help="Optional message template")
@click.pass_context
def wsend(ctx, messenger, data, target, msg_t):
    """Send data or chained items via Messenger endpoint

    \b
    $ diana-cli wsend -t derek.merck@gmail.com --data "msg_text: Hello 123" --msg_t \
        'To: {{ target }}\nFrom: no-reply@example.com\nSubject: Test Message\n\nThe message is "{{msg_text}}"\n\n' \
        smtp:
    """
    click.echo(click.style('Send Data to Target via Messenger', underline=True, bold=True))

    click.echo(pformat(data))
    click.echo(target)

    if msg_t:
        click.echo(msg_t)
        if msg_t.find("\\n"):
            click.echo("Expanding newlines as NL+CR")
            msg_t = msg_t.replace("\\n", "\r\n")
            click.echo(msg_t)

    if data:
        out = messenger.send(data, target=target, msg_t=msg_t)

    if ctx.obj.get("items"):
        for item in ctx.obj.get("items"):
            out = messenger.send(item.asdict(), target=target, msg_t=msg_t)
