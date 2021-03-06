"""
When receiving associated data such as biopsy results from other departments,
they rarely reference the DI assigned accession number and sometimes do not
even use a standardized MRN.

This script reads in two folders of data and attempts to merge them by date and
common patient info (name, date of birth).
"""

import os, csv, logging
from enum import Enum
from glob import glob
from pprint import pprint
from datetime import date, timedelta
from typing import Collection
import attr
from dateutil.parser import parser as DateParser

data_dir = r"D:\Google Drive\Brown\Research\Raw_Data\thyroid_bx_path"
data0_dir = "usbx"
data1_dir = "path"
target_distance = timedelta(days=3)
# data_dir = "/Users/derek/Desktop/thyroid"
# data0_dir = "usbx"
# data1_dir = "path"
# target_distance = timedelta(days=14)

# data_dir = "/Users/derek/Desktop/prostate"
# data0_dir = "mr"
# data1_dir = "path"
# target_distance = timedelta(days=180)


def parse_date(s: str) -> date:
    if not s:
        return
    parser = DateParser()
    dt = parser.parse(s).date()

    if dt.year > 2019:
        dt = dt.replace(year=dt.year - 100)

    return dt


@attr.s(cmp=False, hash=True)
class Patient(object):

    class Sex(Enum):
        MALE = "M"
        FEMALE = "F"
        UNKNOWN = "U"

        @classmethod
        def of(cls, val):
            return cls(val.upper()[0])

    first = attr.ib(type=str)
    last = attr.ib(type=str)
    age = attr.ib(type=int, converter=int)
    sex = attr.ib(converter=Sex.of, default=Sex.UNKNOWN)
    mrn = attr.ib(type=str, default=None)

    def __eq__(self, other: "Patient"):
        if (self.last.upper() == other.last.upper()):
            if (self.first.upper()[0] != other.first.upper()[0]):
                # logging.debug("-> {} matches".format(self.last))
                # logging.debug("   but {} not equal to {}".format(self.first, other.first))
                return False

            elif (self.sex != other.sex and self.sex != Patient.Sex.UNKNOWN
                  and other.sex != Patient.Sex.UNKNOWN):
                # logging.debug("-> {} matches".format(self.last))
                # logging.debug("   and {} equal to {}".format(self.first, other.first))
                # logging.debug("   but {} not equal to {}".format(self.sex, other.sex))
                return False

            elif self.age > 0 and other.age > 0 and (abs(self.age - other.age) > 3):
                # logging.debug("-> {} matches".format(self.last))
                # logging.debug("   and {} equal to {}".format(self.first, other.first))
                # logging.debug("   and {} equal to {}".format(self.sex, other.sex))
                # logging.debug("   but {} not equal to {}".format(self.age, other.age))
                return False

            return True


@attr.s(hash=True)
class SemiIdentifiedStudy(object):
    study_id = attr.ib(type=str)
    study_date = attr.ib(type=date, converter=parse_date)
    patient = attr.ib(type=Patient)
    cancer_status = attr.ib(default=None)
    result = attr.ib(default=None)

    # usbx, path
    def proximal(self, other: "SemiIdentifiedStudy"):
        if self.patient == other.patient:
            if abs(self.study_date - other.study_date) > target_distance or (self.study_date - other.study_date) > timedelta(days=0):
                # logging.debug("-> {} matches, but bx date {} not near path date {}".format(
                #     self.patient.first, self.study_date, other.study_date))
                return False
            return True

    class Factory():

        @classmethod
        def create(cls, **kwargs):

            study_id = kwargs.get("Accession Number") or kwargs.get("AccessionNumber") or kwargs.get("CASE") or kwargs.get("Case Number")
            study_date = kwargs.get("Exam Completed Date") or kwargs.get("ACCESSION DATE") or kwargs.get("StudyDate")
            cancer_status = kwargs.get("Cancer Status")
            result = kwargs.get("Result")

            pfirst = kwargs.get("Patient First Name") or kwargs.get("FIRST")
            plast = kwargs.get("Patient Last Name") or kwargs.get("LAST")
            psex = kwargs.get("Patient Sex") or kwargs.get("SEX") or "Unknown"
            mrn = kwargs.get("Patient MRN") or kwargs.get("PatientID")

            age = kwargs.get("Patient Age")
            if not age:
                pdob = parse_date( kwargs.get("DOB") )
                if pdob:
                    sdt = parse_date( study_date )
                    age = (sdt - pdob).days / 365
                else:
                    age = -1

            patient = Patient(first=pfirst, last=plast, age=age, sex=psex, mrn=mrn)
            study = SemiIdentifiedStudy(study_id=study_id, study_date=study_date,
                                        patient=patient, cancer_status=cancer_status,
                                        result=result)

            return study


def read_folder(path) -> Collection:

    data = set()

    for fp in glob("{}/*.csv".format(path)):

        with open(fp, 'r', newline='', encoding='ISO-8859-1') as f:
            reader = csv.DictReader(f)
            for line in reader:

                if line.get("PatientName"):
                    line["Patient First Name"] = line.get("PatientName").split("^")[1]
                    line["Patient Last Name"] = line.get("PatientName").split("^")[0]

                if "neg" in fp.lower():
                    line["Cancer Status"] = "negative"
                elif "pos" in fp.lower():
                    line["Cancer Status"] = "positive"

                item = SemiIdentifiedStudy.Factory.create(**line)
                data.add(item)

    return data


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    data0 = read_folder(os.path.join(data_dir, data0_dir))
    logging.info("Num studies in {}: {}".format(data0_dir, len(data0)))

    data1 = read_folder(os.path.join(data_dir, data1_dir))
    logging.info("Num studies in {}: {}".format(data1_dir, len(data1)))

    # input("Press any key")
    # pprint(data0)
    #
    # input("Press any key")
    # pprint(data1)
    # exit()

    results = []

    for item0 in data0:
        for item1 in data1:
            # logging.debug("{} items to review".format(len(data1)))
            if item0.proximal(item1):

                pair = {
                    "MRN": item0.patient.mrn,
                    "Accession Number": item0.study_id,
                    "Image Date": item0.study_date,
                    "Path Case": item1.study_id,
                    "Path Date": item1.study_date,
                    "Cancer Status": item1.cancer_status,
                    "Path Result": item1.result
                }

                results.append(pair)
                # data1.remove(item1)
                # break

    logging.info("Num pairs: {}".format(len(results)))

    fieldnames = ["MRN", "Accession Number", "Image Date", "Path Case",
                  "Path Date", "Cancer Status", "Path Result"]

    with open("output_{}daymatch_unrestricted.csv".format(target_distance.days), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
