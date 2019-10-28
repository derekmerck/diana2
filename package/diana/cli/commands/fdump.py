import os
from pathlib import Path
import click
from diana.utils.gateways import ImageFileHandler

@click.command()
@click.argument('format', type=click.Choice(["png"]), default="png")
@click.argument('outpath', default=".", type=click.Path())
@click.pass_context
def fdump(ctx, _format, outpath):
    """Convert and save chained DICOM image data in png format.

    /b
    $ diana-cli get path:/data/dcm IM0001.dcm fdump
    $ ls
    IM0001.png
    """

    click.echo(click.style('Save DICOM as PNG', underline=True, bold=True))

    if not ctx.obj.get("items"):
        ctx.obj["items"] = []

    for item in ctx.obj.get("items"):
        stem = Path(item.meta["FileName"]).stem
        outfile = os.path.join(outpath, f"{stem}.png")
        ImageFileHandler().put(item.get_pixels(), outfile)
