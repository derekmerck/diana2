import click
from diana.apis import DcmDir
from diana.dixel import DixelView
from diana.plus import measure_scout  # monkey patches Dixel


@click.command(short_help="Patient size from localizer")
@click.argument('path', type=click.Path(exists=True))
@click.argument('images', nargs=-1)
def ssde(path, images):
    """Compute patient size from localizer imaging"""

    click.echo(click.style('Measuring scout images', underline=True, bold=True))

    D = DcmDir(path=path)

    for image in images:
        d = D.get(image, view=DixelView.PIXELS)
        result = d.measure_scout()
        click.echo("{} ({}): {}cm".format(image, result[0], round(result[1])))
