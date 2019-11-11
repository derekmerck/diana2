# TODO: This needs refactored for new dispatch model

import click
from typing import Mapping
from crud.cli.utils import ClickEndpoint, CLICK_MAPPING, CLICK_ARRAY
from wuphf.endpoints import SmtpMessenger


@click.command(short_help="Dispatch items to subscribers by channel")
@click.option('--config', '-C',          type=click.File(),
              default="@/subscriptions.yaml")
@click.option('--email-messenger', '-E', type=ClickEndpoint(expects=SmtpMessenger))
# @click.option('--slack-messenger',       type=click.STRING, callback=validate_endpoint)
# @click.option('--sms-messenger',         type=click.STRING, callback=validate_endpoint)
@click.option('--data',                  type=CLICK_MAPPING)
@click.option('--template', '-T',        type=click.File())
@click.option('--channels', '-H',        type=CLICK_ARRAY,
              help="Channel list, use $field to reference item data or meta, like \"$project-$site\"")
@click.option("--dryrun/--wetrun", "-D/-W", default=True)
@click.pass_context
def dispatch(ctx, config, email_messenger: SmtpMessenger, slack_messenger, sms_messenger,
             data: Mapping, template, channels, dryrun: bool):
    """Dispatch data or chained items to subscribers by channel
    
    \b
    $ wuphf-cli dispatch --config subscriptions.yaml
                         --email-messenger gmail::
                         --data "msg_text: Hello 123"
                         --template "{{ msg_text }}"
                         --channels testing

    \b
    $ wuphf-cli get path:/hobit/site_xxx IM00001.dcm
                setmeta "project: hobit"
                dispatch -E gmail::
                         -T "Found {{ AccessionNumber }} in {{ FileName }}"
                         -H 'testing,$project'
    """

    import yaml
    import string

    channels_desc, subs_desc = yaml.safe_load_all(config)

    from wuphf.daemons import Dispatcher
    dispatch = Dispatcher(
        channels_desc=channels_desc,
        subscribers_desc=subs_desc,
    )

    msg_t = template.read()
    email_messenger.msg_t=msg_t
    dispatch.add_messenger("email", email_messenger)

    click.echo(click.style('Calling dispatcher put({}) method'.format(channels),
                           underline=True, bold=True))

    def substitute_channels(_channels, _data):
        rv = []
        for ch in _channels:
            if ch.find("$")>=0:
                ch = string.Template(ch).substitute(**_data)
            rv.append(ch)
        return rv

    if data:
        # Substitute in channels
        _channels = substitute_channels(channels, data)
        out = dispatch.put(data, channels=_channels)

    if ctx.obj.get("items"):
        for item in ctx.obj["items"]:
            _channels = substitute_channels(channels, {**item.meta, **item.tags})
            out = dispatch.put(item.asdict(), channels=_channels)

    click.echo(click.style('Running dispatcher queue', underline=True, bold=True))
    out = dispatch.handle_queue(dryrun=dryrun)
