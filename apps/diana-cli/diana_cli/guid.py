from pprint import pformat
import click
from diana.utils.guid import GUIDMint
from diana.utils.dicom import dicom_date, dicom_name

epilog = """
\b
$ python3 diana-cli.py guid "MERCK^DEREK^L" --age 30
Generating GUID
------------------------
WARNING:GUIDMint:Creating non-reproducible GUID using current date
{'BirthDate': datetime.date(1988, 11, 20),
 'ID': 'VXNQHHN523ZQNJFIY3TXJM4YXABTL6SL',
 'Name': ['VANWASSENHOVE', 'XAVIER', 'N'],
 'TimeOffset': datetime.timedelta(-47, 82822)}
"""


@click.command(short_help="Generate a GUID", epilog=epilog)
@click.argument('name', type=click.STRING)
@click.argument('dob', required=False, type=click.DateTime())
@click.argument('gender', required=False, type=click.STRING, default="U")
@click.option('--age', type=int, help="Substitute age and ref date for DOB")
@click.option('--reference_date', type=click.DateTime(), help="Reference date for AGE")
@click.pass_context
def guid(ctx, name, dob, gender, age, reference_date):
    """Generate a globally unique sham ID from NAME, DOB, and GENDER."""

    click.echo(click.style('Generating GUID', underline=True, bold=True))

    sham = GUIDMint.get_sham_id(name=name, dob=dob, gender=gender,
                                age=age, reference_date=reference_date)

    resp = {
        "name": dicom_name(sham['Name']),
        "birth_date": dicom_date(sham["BirthDate"]),
        "id": sham["ID"],
        "time_offset": sham["TimeOffset"].__str__()
    }

    click.echo(pformat(resp))