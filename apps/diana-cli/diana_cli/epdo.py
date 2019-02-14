import yaml
import click
from pprint import pformat
from diana.utils.endpoint import Serializable
from diana.apis import *


@click.command(short_help="Call endpoint method")
@click.argument('endpoint', type=click.STRING)
@click.argument('method', type=click.STRING)
@click.option('--args', '-g', type=click.STRING, default=None)
@click.option('--mapped_arg', '-m', type=click.STRING, default=None)
@click.option('--kwargs', '-k', type=click.STRING, default=None)
@click.option('--anonymize', '-a', is_flag=True, default=False, help="(ImageDir only)")
@click.option('--subpath_depth', '-b', type=int, default=0, help="Number of sub-directories to use (*Dir Only)")
@click.pass_context
def epdo(ctx, endpoint, method, args, map_arg, kwargs, anonymize, subpath_depth):
    """Call ENDPOINT METHOD with *args and **kwargs.
    Use "path:" for a DcmDir ep and "ipath:" for an ImageDir epp.

     \b
     $ diana-cli epdo orthanc info
     $ diana-cli epdo ipath:/data/images exists -g my_file_name
     """
    services = ctx.obj.get('services')

    click.echo(click.style('Calling endpoint method', underline=True, bold=True))

    if endpoint.startswith("path:"):
        # make a dicom dir
        ep = DcmDir(path=endpoint[5:], subpath_width=2, subpath_depth=subpath_depth)

    elif endpoint.startswith("ipath:"):
        # make an image dir
        ep = ImageDir(path=endpoint[6:], subpath_width=2, subpath_depth=subpath_depth, anonymizing=anonymize)

    elif not services.get(endpoint):
        click.echo(click.style("No such service {}".format(endpoint), fg="red"))
        exit(1)

    else:
        ep = Serializable.Factory.create(**services[endpoint])

    _args = []
    if args:
        _args = [args]
    elif map_arg:
        _args = yaml.load(map_arg)
        if not isinstance(_args, list):
            _args = [_args]

    _kwargs = {}
    if kwargs:
        _kargs = yaml.load(kwargs)

    if hasattr(ep, method):

        out = getattr(ep, method)(*_args, **_kwargs)

        if out:
            click.echo(pformat(out))
        else:
            click.echo(click.style("No response", fg="red"))
            exit(2)

    else:
        click.echo(click.style("No such method {}".format(method), fg="red"))
        exit(1)
