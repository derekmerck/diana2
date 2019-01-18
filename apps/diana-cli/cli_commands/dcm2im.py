from pathlib import Path
import click
from diana.apis import DcmDir
from diana.utils.gateways import ImageFileHandler, DcmFileHandler

@click.command(short_help="Convert DICOM to image")
@click.argument('inpath', type=click.Path(exists=True))
@click.argument('outpath', default=".", type=click.Path())
@click.pass_context
def dcm2im(ctx, inpath, outpath):
    """Convert a DICOM file or directory of files at INPATH into
    pixels and save result in a standard image format (png, jpg)
    at OUTPATH."""

    services = ctx.obj.get('services')
    click.echo('Covert DICOM to Image')
    click.echo('------------------------')

    def convert_file(infile: Path, outfile: Path):
        dixel = DcmDir().get(infile, get_pixels=True)
        ImageFileHandler().put(dixel.get_pixels(), outfile)

    _inpath = Path(inpath)
    _outpath = Path(outpath)

    if _inpath.is_file():
        fni = _inpath
        if _outpath.suffix in [".png", ".jpg"]:
            # outpath is a file
            fno = _outpath
        elif _outpath.is_dir():
            # outpath is a dir
            fno = _outpath / _inpath.with_suffix(".png").name
        else:
            raise ValueError("Output path must be *.png/*.jpg or a directory")
        convert_file(fni, fno)

    if _inpath.is_dir():

        if not _outpath.is_dir():
            raise ValueError("Output path must be a directory for a directory input path")

        infiles = _inpath.glob("*.dcm")

        for fn in infiles:
            fni = _inpath / fn
            fno = _outpath / fn.with_suffix(".png")
            convert_file(fni, fno)

