# Specialized orthanc put with anonymize and tag

import click
from crud.cli.utils import validate_endpoint, validate_dict, validate_array
from diana.apis import Orthanc

@click.command()
@click.argument("dest", callback=validate_endpoint, type=click.STRING)
@click.option("-a", "--anonymize", default=False, is_flag=True,
              help="Anonymize instances as they are uploaded")
@click.option("--anon-salt", default=None, type=click.STRING, envvar="DIANA_ANON_SALT",
              help="Anonymization salt")
@click.option("--sign", type=click.STRING, callback=validate_dict, default=None,
              help="Signature key(s) and elements")
@click.option("--fkey", type=click.STRING, envvar="DIANA_FKEY",
              help="Fernet key for encrypting metadata")
@click.pass_context
def cli(ctx, dest: Orthanc, anonymize, anon_salt, sign, fkey):
    """Put chained instances in orthanc"""
    click.echo(click.style('Putting Instances in Orthanc', underline=True, bold=True))

    from diana.dixel import ShamDixel
    from diana.utils.dicom import DicomLevel as DLV

    if sign and not fkey:
        click.echo("Fernet key required to sign source item")

    for item in ctx.obj.get("items", []):
        dest.put(item)

        if anonymize:
            anon = ShamDixel.from_dixel(item, salt=anon_salt)
            f = dest.anonymize(item, replacement_map=anon.orthanc_sham_map())
            anon.file = f
            dest.put(anon)
            dest.delete(item)

            if sign:
                for sig_key, sig_elements in sign.items():
                    sig_value = item.pack_fields(fkey, sig_elements)
                    dest.putm(anon.sham_parent_oid(DLV.STUDIES), level=DLV.STUDIES, key=sig_key, value=sig_value)
