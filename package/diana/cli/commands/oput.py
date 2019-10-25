# Specialized orthanc put with anonymize and tag

import click
from typing import Mapping
from crud.cli.utils import CLICK_MAPPING, ClickEndpoint
from diana.apis import Orthanc
from diana.dixel import ShamDixel
from diana.utils.dicom import DicomLevel as DLV


@click.command()
@click.argument("dest", type=ClickEndpoint(expects=Orthanc))
@click.option("-a", "--anonymize", default=False, is_flag=True,
              help="Anonymize instances as they are uploaded")
@click.option("--anon-salt", type=click.STRING, default=None, envvar="DIANA_ANON_SALT",
              help="Anonymization salt")
@click.option("--sign", type=CLICK_MAPPING, default=None,
              help="Signature key(s) and elements")
@click.option("--fkey", type=click.STRING, envvar="DIANA_FKEY",
              help="Fernet key for encrypting metadata")
@click.pass_context
def oput(ctx, dest: Orthanc, anonymize: bool, anon_salt, sign: Mapping, fkey):
    """Put chained instances in orthanc"""
    click.echo(click.style('Putting Instances in Orthanc', underline=True, bold=True))

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
                    dest.putm(anon.sham_parent_oid(DLV.STUDIES),
                              level=DLV.STUDIES, key=sig_key, value=sig_value)
