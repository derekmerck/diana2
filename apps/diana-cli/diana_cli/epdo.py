import yaml
import click
from pprint import pformat
from diana.utils.endpoint import Serializable
from diana.apis import *


@click.command(short_help="Call endpoint method")
@click.argument('method', type=click.STRING)
@click.argument('endpoint', type=click.STRING)
@click.option('--kwargs', '-k', type=click.STRING)
@click.option('--anonymize', '-a', is_flag=True, default=False)
@click.pass_context
def epdo(ctx, method, endpoint, kwargs, anonymize):
    """Call METHOD on ENDPOINT.  Use "path:" for a DcmDir ep and "ipath:" for an
     ImageDir epp.
     \b
     $ diana-cli epdo info orthanc
     $ diana-cli epdo ipath:/data exists -k '{"item":"my_file_name"}'
     """
    services = ctx.obj.get('services')

    click.echo(click.style('Calling endpoint method', underline=True, bold=True))

    if endpoint.startswith("path:"):
        # make a dicom dir
        ep = DcmDir(path=endpoint[5:])

    elif endpoint.startswith("ipath:"):
        # make an image dir
        ep = ImageDir(path=endpoint[6:], anonymizing=anonymize)

    elif not services.get(endpoint):
        click.echo(click.style("No such service {}".format(endpoint), fg="red"))
        exit(1)

    else:
        ep = Serializable.Factory.create(**services[endpoint])

    if kwargs:
        _kargs = yaml.load(kwargs)
    else:
        _kwargs = {}

    print(kwargs)

    if hasattr(ep, method):

        out = getattr(ep, method)(**_kwargs)

        if out:
            click.echo(pformat(out))
        else:
            click.echo(click.style("No response", fg="red"))
            exit(2)

    else:
        click.echo(click.style("No such method {}".format(method), fg="red"))
        exit(1)
