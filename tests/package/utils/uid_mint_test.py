from diana.utils.dicom import DicomUIDMint

def test_uid():
    umint = DicomUIDMint()
    s = umint.uid("patient", "study", "series", "instance")
    assert (s == "1.2.826.0.1.3680043.10.43.62.7834598798.958245076358.6951.1763")

    umint = DicomUIDMint("Diana")
    s = umint.uid("patient", "study", "series", "instance")
    assert (s == "1.2.826.0.1.3680043.10.43.1.7834598798.958245076358.6951.1763")


if __name__ == "__main__":
    test_uid()