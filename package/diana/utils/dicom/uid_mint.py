import attr
import hashlib


def hash2int(h, digits):
    return int(h.hexdigest(), 16) % (10 ** digits)


def hash_str(s, digits=2):
    return str(hash2int(hashlib.sha1(str(s).encode("UTF8")), digits))


@attr.s
class DicomUIDMint(object):
    # RIH 3d Lab prefix within the medicalconnections.co.uk namespace
    prefix = "1.2.826.0.1.3680043.10.43"
    """
    1 - iso
    2 - ansi
    840 - us
    0.1.3680043.10.43 - sub-organization within medicalconnections.co.uk

    A 25 character prefix leaves 39 digits and stops available (64 chars max)
    """

    app_id = attr.ib(converter=hash_str, default="dicom")

    def hierarchical_suffix(self, PatientID: str, StudyInstanceUID: str,
                            SeriesInstanceUID=None, SOPInstanceUID=None):

        """
        A hierarchical asset uid has the form:

          `prefix.app.patient.study.series.instance`

        Where
          - prefix = 25 digits                              25
          - app = stop + 2 digits                       3 = 28
          - pt, study = stop + 12 digits each          26 = 54
          - series, instance = stop + 4 digits each (optional)
                                                       10 = 64
        Total length is 64
        """

        entries = []

        entries.append(hash_str(PatientID, 12))
        entries.append(hash_str(StudyInstanceUID, 12))

        if SeriesInstanceUID:
            entries.append(hash_str(SeriesInstanceUID, 4))

            if SOPInstanceUID:
                entries.append(hash_str(SOPInstanceUID, 4))

        return ".".join(entries)



    def uid(self, PatientID: str = None,
            StudyInstanceUID: str = None,
            SeriesInstanceUID=None,
            SOPInstanceUID=None):
        """
        app fields immediately following prefix with 2 digits are
        asset or common uids (pt, st, ser, inst).

        asset_uid takes up to 4 parameters (pt, st, ser, inst) that
        will be converted to strings and hashed.

        Non-asset uids will have app fields >2 digits.
        """

        suffix = self.hierarchical_suffix(PatientID,
                                          StudyInstanceUID,
                                          SeriesInstanceUID,
                                          SOPInstanceUID)

        return "{}.{}.{}".format(DicomUIDMint.prefix, self.app_id, suffix)




