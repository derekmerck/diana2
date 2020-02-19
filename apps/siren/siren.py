import logging
import sys
import click
import yaml
from crud.manager import EndpointManager
from crud.endpoints import Splunk
from crud.cli.utils import CLICK_MAPPING, ClickEndpoint
from crud.cli.commands import check, ls
from diana import __version__
from diana.apis import DcmDir, Orthanc, ObservableOrthanc, ObservableDcmDir
from wuphf.endpoints import SmtpMessenger
from trial_dispatcher import TrialDispatcher as Dispatcher
from handlers import handle_upload_zip, handle_upload_dir, handle_notify_study, start_watcher
import wuphf.cli.string_descs
import diana.cli.string_descs


@click.group(name="diana-siren")  # Non-chaining commands
@click.version_option(version=__version__, prog_name="diana-siren")
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('-s', '--services', type=CLICK_MAPPING,
              help="Services dict as yaml/json format string or @file.yaml")
@click.pass_context
def cli(ctx, verbose, services):
    """Run diana packages for the siren receiver using a command-line interface."""

    if verbose:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
        logger = logging.getLogger("cli")
        logger.debug("Debug level logging active")
        click.echo('Verbose mode is ON')
    else:
        logging.basicConfig(level=logging.WARNING)

    if verbose:
        click.echo("Using services: {}".format(services))

    # Runner does not instantiate ctx properly
    if not ctx.obj:
        ctx.obj = {}

    service_mgr = EndpointManager(ep_descs=services)

    ctx.obj['services'] = service_mgr

cli.add_command(check)
cli.add_command(ls)


@cli.command(short_help="Upload directory to dicom archive and anonymize")
@click.argument("source", type=ClickEndpoint(expects=DcmDir))
@click.argument("dest",   type=ClickEndpoint(expects=Orthanc))
@click.option("--fkey",   type=click.STRING, envvar="DIANA_FKEY",
              help="Fernet key for signature encryption",
              required=True)
@click.option("--salt",   type=click.STRING, envvar="DIANA_ANON_SALT",
              help="Salt for sham id assignment")
@click.pass_context
def upload_dir(ctx, source: DcmDir, dest: Orthanc, fkey, salt):
    """Upload directory to dicom archive and anonymize

    \b
    $ python3 siren.py upload-dir path:/incoming/hobit/site_xxx orthanc:
    """
    handle_upload_dir(source, dest, fkey=fkey, anon_salt=salt)


@cli.command(short_help="Upload zip file to dicom archive and anonymize")
@click.argument("source", type=ClickEndpoint(expects=DcmDir))
@click.argument("fn",     type=click.STRING)
@click.argument("dest",   type=ClickEndpoint(expects=Orthanc))
@click.option("--fkey",   type=click.STRING, envvar="DIANA_FKEY",
              help="Fernet key for signature encryption",
              required=True)
@click.option("--salt",   type=click.STRING, envvar="DIANA_ANON_SALT",
              help="Salt for sham id assignment")
@click.pass_context
def upload_zip(ctx, source: DcmDir, fn, dest: Orthanc, fkey, salt):
    """Upload zip file to dicom archive and anonymize

    \b
    $ python3 siren upload_dir path:/incoming/hobit/site_xxx mystudy.zip orthanc:
    """
    handle_upload_zip(source, fn, dest, fkey=fkey, anon_salt=salt)


@cli.command(short_help="Dispatch study notification and send meta to indexer")
@click.argument("source", type=ClickEndpoint(expects=Orthanc))
@click.argument("item",   type=click.STRING)
@click.option("--subscriptions", "-S", type=click.File(), default="/subscriptions.yaml",
              help="YAML file with channel and subscriber documents",
              required=True)
@click.option("--email-messenger", "-E", type=ClickEndpoint(expects=SmtpMessenger),
              help="Email messenger endpoint")
@click.option("--email-template", "-T", type=click.File(), default="/notify.txt.j2",
              help="Jinja2 template file for notification message")
@click.option("--dryrun/--wetrun", "-D/-W", default=False)
@click.option("--indexer", "-I", type=ClickEndpoint(expects=Splunk),
              help="Splunk or other indexing service endpoint")
@click.option("--fkey", type=click.STRING, envvar="DIANA_FKEY",
              help="Fernet key for signature encryption",
              required=True)
@click.pass_context
def notify_study(ctx, source: Orthanc, item,
                 subscriptions, email_messenger: SmtpMessenger, email_template, dryrun,
                 indexer: Splunk, fkey):
    """Dispatch study notification and send meta to indexer

    \b
    $ python3 siren notify-study orthanc: xxsa-mple-oidx-xxx \\
                    -S ./subscriptions.yaml \\
                    -E gmail: \\
                    -T ./notify.txt.j2 \\
                    -I splunk:
    """

    dispatcher = None
    if subscriptions:
        ch, subs = yaml.safe_load_all(subscriptions)
        dispatcher = Dispatcher(
            channel_tags=ch
        )
        dispatcher.add_subscribers(subs)
        if email_messenger:
            email_messenger.msg_t = email_template.read()
            dispatcher.email_messenger = email_messenger

    handle_notify_study({"oid": item}, source=source, dispatcher=dispatcher,
                        dryrun=dryrun, indexer=indexer, fkey=fkey)


@cli.command(short_help="Start SIREN watcher")
@click.argument("incoming", type=ClickEndpoint(expects=DcmDir))
@click.argument("orthanc", type=ClickEndpoint(expects=Orthanc))
@click.option("--salt",   type=click.STRING, envvar="DIANA_ANON_SALT",
              help="Salt for sham id assignment")
@click.option("--fkey", type=click.STRING, envvar="DIANA_FKEY",
              help="Fernet key for signature encryption",
              required=True)
@click.option("--subscriptions", "-S", type=click.File(), default="/subscriptions.yaml",
              help="YAML file with channel and subscriber documents",
              required=True)
@click.option("--email-messenger", "-E", type=ClickEndpoint(expects=SmtpMessenger),
              help="Email messenger endpoint")
@click.option("--email-template", "-T", type=click.File(), default="/notify.txt.j2",
              help="Jinja2 template file for notification message")
@click.option("--dryrun/--wetrun", "-D/-W", default=False)
@click.option("--indexer", "-I", type=ClickEndpoint(expects=Splunk),
              help="Splunk or other indexing service endpoint")
@click.option("--index-name", default="dicom",
              help="Indexing service bucket (defaults to 'dicom'")
@click.pass_context
def start_watcher(ctx, incoming: DcmDir,
                  orthanc: ObservableOrthanc, salt, fkey,
                  subscriptions, email_messenger: SmtpMessenger, email_template, dryrun,
                  indexer: Splunk, index_name):
    """Run watcher to monitor incoming directory path, anonymize and upload studies,
    email notifications and send meta to indexer

    \b
    $ python3-siren start-watcher \\
                    path:/data/incoming \\
                    orthanc: \\
                    -S ./subscriptions.yaml \\
                    -E gmail: \\
                    -T ./notify.txt.j2 \\
                    -I splunk:
    """

    dispatcher = None
    if subscriptions:
        ch, subs = yaml.safe_load_all(subscriptions)
        dispatcher = Dispatcher(channel_tags=ch)
        dispatcher.add_subscribers(subs)
        if email_messenger:
            email_messenger.from_addr = "siren-ops@umich.edu"
            email_messenger.msg_t = email_template
            dispatcher.email_messenger = email_messenger

    start_watcher(
        incoming,
        orthanc,
        fkey=fkey,
        anon_salt=salt,
        dispatcher=dispatcher,
        dryrun=dryrun,
        indexer=indexer,
        index_name=index_name
    )


# Indirection to set envar prefix from setuptools entry pt
def main():
    cli(auto_envvar_prefix='DIANA', obj={})


if __name__ == "__main__":
    main()
