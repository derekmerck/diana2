import yaml
import click
from pprint import pformat
import requests
from crud.abc import Serializable
from diana.apis import DcmDir
from diana.dixel import Dixel

try:
    from wuphf.endpoints import SmtpMessenger
except ImportError:
    print("WARNING: `message` unavailable; WUPHF pkg missing!")


@click.command(short_help="Send templated message based on dixel data")
@click.argument('dixel', type=click.STRING)
@click.argument('messenger', type=click.STRING)
@click.option('--to_addrs', '-t', thpe=click.STRING)
@click.option('--msg_tmpl', '-m', type=click.STRING)
@click.option('--msg_tmpl_file', '-M', type=click.STRING)
@click.option('--dryrun', '-D', is_flag=True, help="Print string and exit")
@click.pass_context
def message(ctx, messenger, dixel, to_addrs, template, template_file, meta, dryrun):
    """Call MESSENGER SEND with data from **DIXEL.meta and **META.

     DIXEL may be a local path to an instance or a curl command to an Orthanc

     \b
     $ diana-cli message smtp path:/data/images/my_file.dcm \
       -m "{{ tags.accession_number }}" -t "test@example.com"
     $ diana-cli message smtp http:orthanc:orthanc@host/studies/oid... \
       -m "{{ tags.accession_number }}" -t "test@example.com"
    """
    services = ctx.obj.get('services')

    click.echo(click.style('Calling messenger send', underline=True, bold=True))

    if dixel.startswith("path:"):
        D = DcmDir()
        d = D.get(dixel)
    elif dixel.startswith("http"):
        resp = requests.get(dixel)
        if resp:
            d = Dixel.from_orthanc(resp.json())
    else:
        click.echo(click.style("No such dixel {}".format(dixel), fg="red"))
        exit(1)

    if not services.get(messenger):
        click.echo(click.style("No such service {}".format(messenger), fg="red"))
        exit(1)

    _messenger = SmtpMessenger(**services[messenger])

    _messenger.send(d, to_addrs=to_addrs, msg_t=template, dryrun=dryrun)

    if dryrun:
        click.echo(messenger.get(d, to_addrs=to_addrs, msg_t=template))
