from pprint import pprint
import typing as typ
import sys
from diana.dixel import Dixel, Provenance, DixelHashes, huid_sham_map
from diana.apis import DcmDir
from diana.utils.dicom import DicomLevel


#TODO: No test here -- needs test data

def inventory_directory(fp: str, institution: str):

    D = DcmDir(path=fp)
    P = Provenance(institution=institution)

    def register_collection(d: Dixel, lvl: DicomLevel):

        if lvl == DicomLevel.SERIES:
            tags = [d.tags["StudyInstanceUID"],
                    d.tags["SeriesInstanceUID"]]
        else:
            tags = [d.tags["StudyInstanceUID"]]

        sh = DixelHashes.hash_meta(tags)
        key = sh[0:8]

        if collections.get(key) is None:
            col_summary = {
                "Institution": d.meta["Provenance"].institution,
                "PatientID": d.tags["PatientID"],
                "NewPatientID": d.meta["ShamMap"]["Replace"]["PatientID"],
                "AccessionNumber": d.tags["AccessionNumber"],
                "NewAccessionNumber":
                    d.meta["ShamMap"]["Replace"]["AccessionNumber"],
                "StudyDateTime": d.meta["StudyDateTime"],
                "StudyInstanceUID": d.tags["StudyInstanceUID"],
                "MetaHash": sh,
                "DataHash": d.meta["Hashes"].data_hash,
                "NumInstances": 1,
                "CollectionType": str(lvl)
            }
            if lvl == DicomLevel.SERIES:
                col_summary["SeriesInstanceUID"] = d.tags["SeriesInstanceUID"]
            collections[key] = col_summary
        else:
            collections[key]["NumInstances"] += 1
            collections[key]["DataHash"] = DixelHashes.xor_hashes(
                collections[key]["DataHash"], h.data_hash)

    def register_instance(inst: Dixel):
        inst_summary = {
            "Institution": d.meta["Provenance"].institution,
            "PatientID": d.tags["PatientID"],
            "NewPatientID": d.meta["ShamMap"]["Replace"]["PatientID"],
            "AccessionNumber": d.tags["AccessionNumber"],
            "NewAccessionNumber": d.meta["ShamMap"]["Replace"]["AccessionNumber"],
            "StudyDateTime": d.meta["StudyDateTime"],
            "StudyInstanceUID": d.tags["StudyInstanceUID"],
            "SeriesInstanceUID": d.tags["SeriesInstanceUID"],
            "SOPInstanceUID": d.tags["SOPInstanceUID"],
            "MetaHash": d.meta["Hashes"].meta_hash,
            "DataHash": d.meta["Hashes"].data_hash,
            "FileHash": d.meta["Hashes"].file_hash
        }
        key = d.meta["Hashes"].meta_hash[0:8]
        insts[key] = inst_summary

    insts = {}
    collections = {}

    # TODO: assert that the final series ID is the same with
    #       files or reversed(files)

    for f in D.files('*')[0:10]:
        d = D.get(f, file=True, pixels=True)
        if d is None:
            continue

        h = DixelHashes()
        h.set_meta_hash([d.tags["StudyInstanceUID"],
                         d.tags["SeriesInstanceUID"],
                         d.tags["SOPInstanceUID"]])
        h.set_data_hash(d.get_pixels())
        h.set_file_hash(d.file)
        d.meta["Hashes"] = h
        d.meta["Provenance"] = P

        s = huid_sham_map(d)
        d.meta["ShamMap"] = s

        register_instance(d)
        register_collection(d, DicomLevel.SERIES)
        register_collection(d, DicomLevel.STUDIES)

    return insts, collections


if __name__ == "__main__":

    fp = sys.argv[1]
    inst = sys.argv[1].split('/')[-1].capitalize()

    insts, collections = inventory_directory(fp, inst)

    # print("INSTANCES")
    # print("================")
    # pprint(insts)
    #
    # print("COLLECTIONS")
    # print("================")
    # pprint(collections)

    studies = {k: collections[k]
               for k, v in collections.items()
                 if v["CollectionType"] == "studies"}

    # print("STUDIES")
    # print("================")
    # pprint(studies)

    def pluck(k: str, l: typ.List[typ.Dict], unique=False):
        values = [d[k] for d in l]
        if unique:
            values = list( set(values) )
        return values

    results = {}

    institutions = pluck( "Institution", studies.values(), unique=True )

    for i in institutions:
        studies_ = [s for s in studies.values() if s["Institution"] == i]
        patients = pluck( "PatientID", studies_, unique=True )

        results[i] = {}

        for p in patients:
            studies__ = [s for s in studies_ if s["PatientID"] == p]

            summaries = []
            for s in studies__:
                summary = {"OriginalAccessionNumber": s["AccessionNumber"],
                           "OriginalDateTime": s["StudyDateTime"].isoformat(),
                           "NewPatientID": s['NewPatientID'],
                           "NewAccessionNumber": s["NewAccessionNumber"],
                           "NumInstances": s["NumInstances"]
                          }
                summaries.append(summary)

            results[i][p] = summaries

    pprint(results)