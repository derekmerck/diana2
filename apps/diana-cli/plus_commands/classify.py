import os
import click
from diana.apis import DcmDir
from diana.dixel import DixelView
from diana.plus.halibut import get_mobilenet

epilog = """
\b
$ diana-plus classify resources/models/view_classifier/view_classifier.h5 tests/resources/dcm IM2263
Classifying images
------------------
Predicted: negative (0.88)
"""


@click.command(short_help="Classify DICOM files", epilog=epilog)
@click.argument('model', type=click.File())
@click.argument('path', type=click.Path(exists=True))
@click.argument('images', nargs=-1)
@click.option("--positive", "-p", help="Positive class", default="positive")
@click.option("--negative", "-n", help="Negative class", default="negative")
def classify(model, path, images, positive, negative):
    """Apply a classification MODEL to PATH with IMAGES"""

    click.echo(click.style('Classifying images', underline=True, bold=True))

    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    _model = get_mobilenet(0, weights=None)
    _model.load_weights(model.name)

    D = DcmDir(path=path)

    for image in images:
        d = D.get(image, view=DixelView.PIXELS)
        # prediction = get_prediction( model, image )
        prediction = d.get_prediction(_model)

        if prediction >= 0.5:
            click.echo("Predicted: {} ({})".format( positive, round(prediction, 2) ))
        else:
            click.echo("Predicted: {} ({})".format( negative, round(1.0-prediction, 2) ))
