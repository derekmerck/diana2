from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
from hashlib import md5
from itertools import count
import random
import attr
import pydicom
from diana.dixel import Dixel
from diana.utils.dicom import DicomLevel, dicom_date, dicom_time, dicom_name, DicomUIDMint
from diana.utils.guid import GUIDMint


dcm_mint = DicomUIDMint("diana-mock")


@attr.s(hash=False)
class MockInstance(Dixel):

    inst_num = attr.ib(default=0)

    instuid = attr.ib(init=False)
    @instuid.default
    def set_instuid(self):
        return dcm_mint.uid(self.parent.tags['PatientID'],
                            self.parent.tags['AccessionNumber'],
                            self.parent.tags['SeriesNumber'],
                            self.inst_num)

    inst_datetime = attr.ib( init=False )
    @inst_datetime.default
    def set_inst_datetime(self):
        if len( self.parent.children ) > 0:
            ref_time = self.parent.children[-1].inst_datetime
        else:
            ref_time = self.parent.series_datetime
        secs_delta = random.randint(1,2)
        return ref_time + timedelta(seconds=secs_delta)

    level = attr.ib( init=False, default=DicomLevel.INSTANCES )

    def __attrs_post_init__(self):

        self.meta = {
            **self.parent.meta,
            "InstanceDateTime": self.inst_datetime
        }
        self.tags = {
            **self.parent.tags,
            "InstanceNumber": self.inst_num,
            "SOPInstanceUID": self.instuid,
            "InstanceCreationDate": dicom_date(self.inst_datetime),
            "InstanceCreationTime": dicom_time(self.inst_datetime)
        }

    def __str__(self):
        return "{}-{:02}-{:03}: {:64} : {:10} / {:10}".format(
            self.tags["AccessionNumber"][0:4],
            self.tags["SeriesNumber"],
            self.tags["InstanceNumber"],
            self.tags["SOPInstanceUID"],
            self.tags["StudyDescription"],
            self.tags["SeriesDescription"]
        )


    def as_pydicom_ds(self):
        """
        Return a pydicom dataset suitable for writing to disk.  This is primarily useful
        for dixel-mocking.
        """

        if self.level < DicomLevel.INSTANCES:
            raise TypeError("Can only convert DICOM instances to pydicom datasets")

        ds = pydicom.Dataset()

        ds.PatientName = self.tags["PatientName"]
        ds.PatientID = self.tags["PatientID"]
        ds.PatientBirthDate = self.tags["PatientBirthDate"]
        ds.PatientSex = self.tags["PatientSex"]

        ds.AccessionNumber = self.tags["AccessionNumber"]
        ds.InstitutionName = self.tags["Institution"]
        ds.Modality = self.tags["Modality"]
        ds.StationName = self.tags["StationName"]
        ds.Manufacturer = self.tags["Manufacturer"]
        ds.ManufacturerModelName = self.tags["ManufacturerModelName"]
        ds.ContentDate = self.tags["StudyDate"]
        ds.ContentTime = self.tags["StudyTime"]

        ds.StudyDescription = self.tags["StudyDescription"]
        ds.StudyInstanceUID = self.tags["StudyInstanceUID"]
        ds.StudyDate = self.tags["StudyDate"]
        ds.StudyTime = self.tags["StudyTime"]

        ds.SeriesInstanceUID = self.tags["SeriesInstanceUID"]
        ds.SeriesDescription = self.tags["SeriesDescription"]
        ds.SeriesNumber = self.tags["SeriesNumber"]
        ds.SeriesDate = self.tags["SeriesDate"]
        # ds.SeriesCreationTime = self.tags["SeriesTime"]
        ds.SeriesTime = self.tags["SeriesTime"]

        ds.SOPInstanceUID = self.tags["SOPInstanceUID"]
        ds.InstanceNumber = self.tags["InstanceNumber"]
        ds.InstanceCreationDate = self.tags["InstanceCreationDate"]
        ds.InstanceCreationTime = self.tags["InstanceCreationTime"]

        # Set the transfer syntax
        ds.is_little_endian = True
        ds.is_implicit_VR = True

        # ds.Status = 0

        return ds

    def gen_file(self, fn=None):

        # print("Setting file meta information...")
        # Populate required values for file meta information
        file_meta = pydicom.Dataset()
        file_meta.FileMetaInformationGroupLength = 60  # Will be rewritten but must exist
        file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT
        file_meta.MediaStorageSOPInstanceUID = "1.2.3"
        file_meta.ImplementationClassUID = "1.2.3.4"

        # Wants all of these to be legit:
        #   * (0002,0000) FileMetaInformationGroupLength, UL, 4
        #   * (0002,0001) FileMetaInformationVersion, OB, 2
        # X * (0002,0002) MediaStorageSOPClassUID, UI, N
        # X * (0002,0003) MediaStorageSOPInstanceUID, UI, N
        #   * (0002,0010) TransferSyntaxUID, UI, N
        # X * (0002,0012) ImplementationClassUID, UI, N

        ds = pydicom.FileDataset(fn, self.as_pydicom_ds(),
                                 file_meta=file_meta,
                                 preamble=b"\0" * 128)

        # print(ds)
        with NamedTemporaryFile() as f:
            ds.save_as(filename=f.name, write_like_original=True)
            self.file = f.read()
            # print(self.file)



@attr.s(hash=False)
class MockSeries(Dixel):

    ser_num = attr.ib(default=0)
    ser_desc = attr.ib(default="DICOM Series")
    n_instances = attr.ib(default=1)

    series_datetime = attr.ib(init=False)
    @series_datetime.default
    def set_series_datetime(self):
        if len( self.parent.children ) > 0:
            ref_time = self.parent.children[-1].children[-1].inst_datetime
        else:
            ref_time = self.parent.study_datetime
        secs_delta = random.randint(20,100)
        return ref_time + timedelta(seconds=secs_delta)

    seruid = attr.ib(init=False)
    @seruid.default
    def set_seruid(self):
        return dcm_mint.uid(
            self.parent.tags['PatientID'],
            self.parent.tags['AccessionNumber'],
            self.ser_num)

    level = attr.ib(init=False, default=DicomLevel.SERIES)

    def __attrs_post_init__(self):

        self.meta = {
            **self.parent.meta,
            "SeriesDateTime": self.series_datetime
        }
        self.tags = {
            **self.parent.tags,
            "SeriesDescription": self.ser_desc,
            "SeriesNumber": self.ser_num,
            "SeriesInstanceUID": self.seruid,
            "SeriesDate": dicom_date(self.series_datetime),
            "SeriesTime": dicom_time(self.series_datetime)
        }

        for i in range(1, self.n_instances+1):
            self.children.append( MockInstance(parent=self,
                                               inst_num=i) )

@attr.s
class MockStudy(Dixel):
    """This is a study-level root dixel"""
    n_dixels = count(0)
    dxid = attr.ib(init=False, factory=n_dixels.__next__)

    study_datetime=attr.ib(factory=datetime.now, type=datetime)
    site_name=attr.ib(default="Mock Site", type=str)
    station_name=attr.ib(default="Scanner", type=str)
    modality=attr.ib(default="CT", type=str)

    gender = attr.ib(init=False)
    @gender.default
    def setup_gender(self):
        return random.choice(["M", "F"])

    study_description=attr.ib(init=False)
    @study_description.default
    def set_study_description(self):
        anatomy = random.choice(["HEAD",
                                 "NECK",
                                 "EXTREMITY",
                                 "PELVIS",
                                 "CHEST",
                                 "ABDOMEN"])
        contrast = random.choice(["NC", "WIVC", "WWOIVC"])
        code = 0
        for c in self.modality + anatomy + contrast:
            code += ord(c)

        result = "IMG{} {} {} {}".format(code, self.modality, anatomy, contrast)
        return result

    # Need patient id to mock accession num
    stuid = attr.ib(init=False)

    level = attr.ib(init=False, default=DicomLevel.STUDIES)

    def __attrs_post_init__(self):
        patient_info = GUIDMint.get_sham_id(
                name=self.dxid,
                age=random.randint(18, 85),
                gender=self.gender,
                reference_date=self.study_datetime
            )
        hash_str = patient_info["ID"] + self.study_datetime.isoformat()
        accession_num = md5(hash_str.encode("UTF-8")).hexdigest()

        self.stuid = dcm_mint.uid(patient_info["ID"], accession_num)

        self.meta = {
            "StudyDateTime": self.study_datetime
        }
        self.tags = {
            "AccessionNumber": accession_num,
            "PatientName": dicom_name(patient_info["Name"]),
            "PatientID": patient_info["ID"],
            "PatientSex": str(self.gender).upper(),
            "PatientBirthDate": dicom_date(patient_info["BirthDate"]),
            "StudyInstanceUID": self.stuid,
            "StudyDescription": self.study_description,
            "StationName": self.station_name,
            "Manufacturer": "Device Manufacturer",
            "ManufacturerModelName": "Device Model Name",
            "Institution": self.site_name,
            "Modality": self.modality,
            "StudyDate": dicom_date(self.study_datetime),
            "StudyTime": dicom_time(self.study_datetime)
        }

        distribution = {
            # Mod  SeriesDesc    NSer  NInst  P of at least one
            "CT": [("Localizer", 2, 2, 1, 1),
                   ("Volume",    1, 3, 30, 200),
                   ("Fluoro",    0, 1, 10, 50, 0.2),
                   ("Reformat",  0, 2, 100, 200, 0.2),
                   ("Dose Report", 1, 1, 1, 1)],
            "MR": [("Localizer", 1, 3, 1, 1),
                   ("Sequence",  3, 6, 10, 50),
                   ("Diffusion Map", 0, 1, 1, 1, 0.2)],
            "CR": [("PA",        1, 1, 1, 1),
                   ("Lateral",   1, 1, 1, 1),
                   ("Bx",        0, 1, 1, 2, 0.2)],
            "US": [("Transverse", 3, 6, 1, 1),
                   ("Sagittal",  3, 6, 1, 1),
                   ("Cine",      1, 3, 30, 50),
                   ("Doppler",   0, 3, 1, 3, 0.2),
                   ("Bx",        0, 2, 3, 5, 0.2)]
        }

        series_defs = distribution[self.modality]

        ser_num = 0
        for s in series_defs:

            if s[0] == 0:
                if random.random < s[5]:
                    num_series_this_type = 1
                else:
                    num_series_this_type = 0
            else:
                num_series_this_type = random.randint(s[1], s[2])

            for i in range(1,num_series_this_type+1):

                ser_num += 1

                if num_series_this_type > 1:
                    ser_desc = "{} {}".format( s[0], i )
                else:
                    ser_desc = s[0]

                n_instances = random.randint( s[3], s[4] )

                S = MockSeries( parent=self,
                                ser_num=ser_num,
                                ser_desc=ser_desc,
                                n_instances=n_instances)
                self.children.append( S )

