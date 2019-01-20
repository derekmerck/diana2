import os, logging, subprocess
from pathlib import Path
from pypandoc import convert_file
import click


@click.command()
@click.argument("path", default=".", type=click.Path(exists=True))
@click.argument("outdir", default=".", type=click.Path())
@click.option("--recurse", is_flag=True, default=False)
def cli(path, outdir, recurse):
    """Convert markdown files at PATH and re-save them in OUTDIR"""

    click.echo('md2rst')

    _path = Path(path).resolve()
    _outdir = Path(outdir).resolve()

    def mk_outfile(fp: Path):
        if fp.name == "README.md":
            name = fp.parent.name + ".rst"
        else:
            name = fp.name[:-3] + ".rst"
        ofp = _outdir / name
        click.echo("Converting {} to {}".format(fp, ofp))
        return ofp

    def _convert_file(infile: Path, fmt: str, outputfile: Path):
        convert_file(str(infile), fmt, outputfile=str(outputfile))

    if not recurse:
        if _path.is_file() and _path.suffix == ".md":
            _convert_file(_path, "rst", outputfile=mk_outfile(_path))
        else:
            raise ValueError("{} is not a valid target".format(_path))

    else:
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if name.endswith('.md'):
                    fp = Path(os.path.join(root, name)).resolve()

                    ignored = not subprocess.call(
                        "git check-ignore {}".format(fp), shell=True)

                    if fp.parent is outdir or ignored:
                        continue
                    _convert_file(fp, "rst", outputfile=mk_outfile(fp))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    cli()



