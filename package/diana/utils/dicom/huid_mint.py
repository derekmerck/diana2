"""
DICOM Hash UID Mint

Derek Merck, Spring 2020

Minting reproducible UIDs is important for anticipating the OIDs of anonymized
studies and for ensuring studies are linked by SeriesUI and StudyUID, even when
individual image instances are anonymized statelessly.

Conversely, tying the InstanceUID to the pixel data hash can help ensure that
multiple copies of identical image data collide at the same DICOM UID space.
"""

from typing import List
import attr
import hashlib
from .levels import DicomLevel as DLv


def hash2int(h, digits):
    return int(h.hexdigest(), 16) % (10 ** digits)


def hash_str(s, digits=2):
    return str(hash2int(hashlib.sha1(str(s).encode("UTF8")), digits))


@attr.s
class DicomHashUIDMint(object):

    prefix: str = "1.2.826.0.1.3680043.10.43"
    """
    Prefix parts:
      - 1 - iso
      - 2 - ansi
      - 840 - us
      - 0.1.3680043.10.43 - sub-organization within medicalconnections.co.uk

    A 25 character prefix leaves 39 digits and stops available (64 chars max)
    """

    # This is the namespace of the mint, it is encoded into each UID
    app_id: str = "dicom"

    @classmethod
    def hashes_from_uid(cls, instance_uid: str) -> List[str]:
        # Convenience function to extract the hex ihash suffix from an inst ihash uid
        if not instance_uid.startswith(DicomHashUIDMint.prefix):
            raise ValueError(f"Bad prefix")
        working_str = instance_uid[len(DicomHashUIDMint.prefix)+1:]

        try:
            app_id, schema, level, *suffix = working_str.split('.')
        except:
            raise ValueError("Not hash uid format")

        if schema != hash_str("hash_uid", 2):
            raise ValueError(f"Schema {schema} is not 'hash_uid'")

        ret = []
        for item in suffix:
            ret.append(str( hex(int(item)) )[2:])
        return ret

    def content_hash_uid(self,
                 hex_hash: str,
                 dicom_level: DLv = DLv.INSTANCES,
                 hex_annotations: list = None,
                 app_id: str = None):
        """
        UID format suitable for validating pixel content regardless of metadata.

        An hash uid has the form:

          `prefix.app.schema.dec_hash{.dec_annotations}`

        Where
          - prefix = 25 digits                              25
          - app = stop + 2 digits                       3 = 28
          - schema = stop + 2 digits                    3 = 31
          - level = stop + 1 digit                      2 = 33
          - 64-bit hash = stop + 20 digits             21 = 54
          - optional annotation = stop + 8 dig         11 = 63 (optional)

        Total length is 53 or 63 chars

        A single instance study will result in the same content hash for
        study, series, and instance.  A single series study will share the
        content hash for both the study and series, so we have to use a
        DICOM-level field (inst=0,ser=1,stu=2) to guarantee uniqueness.

        Similarly, users can force a totally clean UID while maintaining the
        reference content hash suffix for a freshly copied/anonymized image by
        manually setting the app_id to something unique like "anon".

        Annotations are intended to include validation data, like an abbreviated
        series and study content hash for reference, hence they are also passed using
        hexidecimal representation.
        """

        _app_id = hash_str( app_id or self.app_id )
        schema = hash_str("hash_uid", 2)
        level = dicom_level.value
        dec_hash = int(hex_hash, 16)

        uid = f"{DicomHashUIDMint.prefix}.{_app_id}.{schema}.{level}.{dec_hash}"

        if hex_annotations:
            dec_annotations = [str(int(hex_a, 16)) for hex_a in hex_annotations]
            dec_annotations = ".".join(dec_annotations)
            if len(dec_annotations) > 11:  # 2x2 byte annotations
                raise ValueError(f"Annotations are too long in integer format ({len(dec_annotations)})")
            uid += f".{dec_annotations}"

        return uid
