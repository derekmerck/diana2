import click
from diana.apis import DcmDir
from diana.dixel import DixelView
from diana.plus import measure_scout  # monkey patches Dixel

epilog = """
Basic algorithm is to use a 2-element Guassian mixture model to find a threshold
that separates air from tissue across breadth of the image.  Known to fail when 
patients do not fit in the scout field of view.

Returns image orientation and estimated distance in centimeters.  These measurements
can be converted into equivalent water volumes using AAPM-published tables.

\b
$ diana-plus ssde tests/resources/scouts ct_scout_01.dcm ct_scout_02.dcm
Measuring scout images
------------------------
ct_scout_01.dcm (AP): 28.0cm
ct_scout_02.dcm (LATERAL): 43.0cm
"""


@click.command(short_help="Estimate patient size from localizer", epilog=epilog)
@click.argument('path', type=click.Path(exists=True))
@click.argument('images', nargs=-1)
def ssde(path, images):
    """Estimate patient dimensions from CT-localizer IMAGES for size-specific dose estimation."""

    click.echo(click.style('Measuring scout images', underline=True, bold=True))

    D = DcmDir(path=path)

    for image in images:
        d = D.get(image, view=DixelView.PIXELS)
        result = d.measure_scout()
        click.echo("{} ({}): {}cm".format(image, result[0], round(result[1])))
