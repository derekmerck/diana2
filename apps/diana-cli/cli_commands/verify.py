import click
import logging
from pprint import pformat
from dill.source import getsource
from itsdangerous import signer

import diana


@click.command(short_help="Verify DIANA package against signature")
@click.argument("input")
def verify(input):
    pass

