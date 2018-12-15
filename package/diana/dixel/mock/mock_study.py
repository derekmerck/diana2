import os, string, logging, random
from hashlib import md5
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta
import pydicom
import attr
from diana.apis import Dixel
from diana.utils.dicom import DicomUIDMint, DicomLevel, dicom_strfname, dicom_strftime2, dicom_strfdate
from guidmint import PseudoMint

mint = PseudoMint()
umint = DicomUIDMint('diana')  # Put UIDs in diana app namespace

# Some default selections for study parameters

INSTITUTIONS = {
    "RIH": 0.6,
    "TMH": 0.3,
    "NPH": 0.1
}

CONTRAST = {
    'NC': 0.7,
    'C': 0.3
}

MODALITIES = {
    'CR': 0.5,
    'CT': 0.3,
    'MR': 0.1,
    'US': 0.05,
    'NM': 0.05
}

BODY_PART = {
    'HEAD':      0.2,
    'CHEST':     0.4,
    'ABDOMEN':   0.2,
    'EXTREMITY': 0.05,
    'PELVIS':    0.15
}


@attr.s(hash=False)
class MockInstance(Dixel):

    series = attr.ib( default=None )

    inst_num = attr.ib()
    instuid = attr.ib()
    inst_datetime = attr.ib( init=False )
    level = attr.ib( init=False, default=DicomLevel.INSTANCES )

    @inst_num.default
    def get_ser_num(self):
        return len( self.series.instances ) + 1

    @instuid.default
    def set_instuid(self):
        return umint.uid(self.series.study.patient.guid, self.series.study.accession_number, self.series.ser_desc, self.inst_num)

    @inst_datetime.default
    def set_inst_datetime(self):
        if len( self.series.instances ) > 0:
            ref_time = self.series.instances[-1].inst_datetime
        else:
            ref_time = self.series.series_datetime
        secs_delta = random.randint(1,2)
        return ref_time + timedelta(seconds=secs_delta)

    def gen_file(self, fn=None):

        # print("Setting file meta information...")
        # Populate required values for file meta information
        file_meta = pydicom.Dataset()
        file_meta.FileMetaInformationGroupLength = 60 # Will be rewritten but must exist
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

        ds = pydicom.FileDataset(fn, self.pydicom_dataset(),
                                 file_meta=file_meta, preamble=b"\0" * 128)

        # print(ds)
        with NamedTemporaryFile() as f:
            ds.save_as(filename=f.name, write_like_original=True)
            self.file = f.read()
            # print(self.file)


    def pydicom_dataset(self):

        ds = pydicom.Dataset()

        ds.PatientName = dicom_strfname(self.series.study.patient.name)
        ds.PatientID = self.series.study.patient.guid
        ds.PatientBirthDate = dicom_strfdate( self.series.study.patient.dob )
        ds.PatientSex = self.series.study.patient.sex.upper()

        ds.AccessionNumber = self.series.study.accession_number
        ds.InstitutionName = self.series.study.institution
        ds.Modality = self.series.study.modality
        ds.StationName  = self.series.study.station_name
        ds.Manufacturer = "Device Manufacturer"
        ds.ManufacturerModelName = "Device Model Name"
        ds.ContentDate = dicom_strfdate( self.series.study.study_datetime )
        ds.ContentTime = dicom_strftime2( self.series.study.study_datetime )[-1]

        ds.StudyDescription = self.series.study.study_desc
        ds.StudyInstanceUID = self.series.study.stuid
        ds.StudyDate = dicom_strfdate( self.series.study.study_datetime )
        ds.StudyTime = dicom_strftime2( self.series.study.study_datetime )[-1]

        ds.SeriesInstanceUID = self.series.seruid
        ds.SeriesDescription = self.series.ser_desc
        ds.SeriesDate = dicom_strfdate( self.series.study.study_datetime )
        ds.SeriesNumber = self.series.ser_num
        ds.SeriesCreationTime = dicom_strftime2( self.series.series_datetime )[-1]

        ds.SOPInstanceUID = self.instuid
        ds.InstanceNumber = self.inst_num
        ds.InstanceCreationDate = dicom_strfdate(self.inst_datetime)
        ds.InstanceCreationTime = dicom_strftime2(self.inst_datetime)[-1]

        # Set the transfer syntax
        ds.is_little_endian = True
        ds.is_implicit_VR = True

        return ds


@attr.s(hash=False)
class MockSeries(Dixel):

    study = attr.ib( default=None )

    ser_num = attr.ib()
    ser_desc = attr.ib()
    n_instances = attr.ib()
    seruid = attr.ib()
    level = attr.ib( init=False, default=DicomLevel.SERIES )

    instances = attr.ib( init=False, factory=list )
    series_datetime = attr.ib( init=False )

    def __attrs_post_init__(self):
        for i in range(self.n_instances):
            self.instances.append( MockInstance(series = self) )

    @ser_num.default
    def get_ser_num(self):
        return len( self.study.series ) + 1

    @ser_desc.default
    def get_ser_desc(self):
        if (self.study.modality == "CT" or self.study.modality == "MR"):
            num = self.ser_num - 1  # start with scouts
        else:
            num = self.ser_num      # start with primary
        return ['SCOUT',
                'PRIMARY SERIES', 'SECONDARY SERIES', 'REFORMAT 1',
                'REPEAT SERIES', 'REFORMAT 2'][num]

    @n_instances.default
    def set_n_instances(self):
        if (self.study.modality == "CT" or self.study.modality == "MR") and self.ser_num > 1:
            return random.randint(10,50)
        else:
            return random.randint(1,4)

    @seruid.default
    def set_seruid(self):
        return umint.uid(self.study.patient.guid, self.study.accession_number, self.ser_desc)

    @series_datetime.default
    def set_series_datetime(self):
        if len( self.study.series ) > 0:
            ref_time = self.study.series[-1].series_datetime
        else:
            ref_time = self.study.study_datetime
        secs_delta = random.randint(20,100)
        return ref_time + timedelta(seconds=secs_delta)


@attr.s(hash=False)
class MockStudy(Dixel):

    seed = attr.ib(default=None)

    institution = attr.ib()
    modality = attr.ib()
    station_name = attr.ib()
    study_datetime = attr.ib()
    accession_number = attr.ib()

    patient = attr.ib()
    study_desc = attr.ib()

    stuid = attr.ib( init=False )
    level = attr.ib( init=False, default=DicomLevel.STUDIES )

    n_series = attr.ib()
    series = attr.ib( init=False, factory=list )

    def __attrs_post_init__(self):
        for s in range(self.n_series):
            self.series.append( MockSeries(study = self) )

    @seed.validator
    def set_seed(self, attribute, value):
        if value:
            random.seed(value)

    @institution.default
    def set_institution(self):
        return random.choice(list(INSTITUTIONS.keys()))
        # return random.choices(list(INSTITUTIONS.keys()), INSTITUTIONS.values())[0]

    @modality.default
    def set_modality(self):
        return random.choice(list(MODALITIES.keys()))
        # return random.choices(list(INSTITUTIONS.keys()), INSTITUTIONS.values())[0]

    @station_name.default
    def set_station_name(self):
        return "{} device".format(self.modality)

    @study_datetime.default
    def set_study_datetime(self):
        # last 3 days
        secs = 3*24*60*60
        offset = random.randrange(-secs,0)
        return datetime.today()+timedelta(seconds=offset)

    @accession_number.default
    def set_accession_number(self):
        return md5(os.urandom(32)).hexdigest()[0:16]

    @patient.default
    def set_patient(self):
        return MockPatient(self.seed)

    @study_desc.default
    def set_study_desc(self):
        contrast = random.choice(list(CONTRAST.keys()))
        body_part = random.choice(list(BODY_PART.keys()))
        return "{} {} {}".format(self.modality, contrast, body_part)

    @stuid.default
    def set_stuid(self):
        return umint.uid(self.patient.guid, self.accession_number)

    @n_series.default
    def set_n_series(self):
        if self.modality == "CT" or self.modality == "MR":
            return random.randint(2,6)
        else:
            return random.randint(1,3)

    def dixels(self):
        res = set()
        for s in self.series:
            for i in s.instances:
                res.add(i)
        return res


@attr.s
class MockPatient(object):

    seed = attr.ib(default=None)
    sex = attr.ib()
    age = attr.ib()
    guid = attr.ib()
    name = attr.ib()
    dob = attr.ib()
    level = attr.ib( init=False, default=DicomLevel.PATIENTS )

    @seed.validator
    def set_seed(self, attribute, value):
        if value:
            random.seed(value)

    @sex.default
    def pick_sex(self):
        return random.choice(["M", "F"])

    @age.default
    def pick_age(self):
        return random.randint(19,65)

    @guid.default
    def set_guid(self):
        return mint.mint_guid(''.join(random.sample(string.ascii_uppercase + string.digits, k=16)))

    @dob.default
    def set_dob(self):
        return mint.pseudodob(guid=self.guid, age=self.age)

    @name.default
    def set_name(self):
        return mint.pseudonym(guid=self.guid, gender=self.sex)


def write_file(fn, instance):

    instance.gen_file(fn)
    with open(fn, 'wb') as f:
        f.write( instance.file )


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    pp = []
    for seed in range(1,4):
        s = MockStudy(modality='CT')

        data_dir = "/Users/derek/Desktop/dcm/{}".format(s.accession_number)
        os.makedirs(data_dir, exist_ok=True)
        for d in s.dixels():
            fn = "{}-{:0>2}-{:0>2}.dcm".format(
                    d.series.study.accession_number[0:6],
                    d.series.ser_num,
                    d.inst_num)
            write_file(os.path.join(data_dir, fn), d)

            # D = pydicom.read_file(os.path.join(data_dir, fn))
            # logging.debug(D.file_meta)


