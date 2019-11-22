"""
Xnat 1.x DIANA interface

Xnat level   DICOM level   Int
----------   -----------   ---
Project      --             0
Subject      Patient        1
Experiment   Study          2
Scans        Series         3
"""

import logging
from typing import Mapping
import attr
import xmltodict
from pyxnat import Interface as XnatGateway
# Originally implemented using requests directly, not sure if there is a reason to use pyxnat
from crud.abc import Endpoint, Serializable
from diana.dixel import Dixel
from diana.utils.dicom import DicomLevel as Dlv

@attr.s
class Xnat(Endpoint, Serializable):

    # var_dict = {'study_type': 'xnat:mrSessionData/fields/field[name=study_type]/field'}
    protocol = attr.ib(default="http")
    host = attr.ib(default="localhost")
    path = attr.ib(default=None)
    port = attr.ib(default=8080)
    user = attr.ib(default="admin")
    password = attr.ib(default="admin")

    gateway = attr.ib()
    @gateway.default
    def setup_gateway(self):
        return XnatGateway(server=f'{self.protocol}://{self.host}:{self.port}',
                           user=self.user,
                           password=self.password)

    def projects(self):
        return list(self.gateway.select.projects())

    def subjects(self, project_id):
        return list(self.gateway.select.project(project_id).subjects())

    def studies(self, project_id, subject_id):
        return list(self.gateway.select.project(project_id).subject(subject_id).experiments())

    def select_item(self, project_id, subject_id=None, study_id=None):
        if not subject_id:
            return self.gateway.select.project(project_id), 0
        elif not study_id:
            return self.gateway.select.project(project_id).subject(subject_id), Dlv.PATIENTS
        else:
            return self.gateway.select.project(project_id).subject(subject_id).experiment(study_id),\
                   Dlv.STUDIES

    def get(self, item: Dixel, project_id=None, subject_id=None, study_id=None) -> Mapping:

        project_id = item.meta.get("ProjectID") or project_id
        subject_id = item.tags.get("PatientID") or subject_id
        study_id = item.tags.get("AccessionNumber") or study_id
        handle, lvl = self.select_item(project_id, subject_id=subject_id, study_id=study_id)
        ret = handle.get()
        data = xmltodict.parse(ret)

        if lvl == 0:
            data = data.get("xnat:Project")
        elif lvl == Dlv.PATIENT:
            data = data.get("xnat:Subject")
        else:
            data = data.get("xnat:MRSession")

        return data

        # dixel = Dixel.from_xnat(data)
        # return dixel

    def getm(self, item: Dixel, project_id=None, subject_id=None, study_id=None, key=None ):

        project_id = item.meta.get("ProjectID") or project_id
        subject_id = item.tags.get("PatientID") or subject_id
        study_id = item.tags.get("AccessionNumber") or study_id
        handle, lvl = self.select_item(project_id, subject_id, study_id)

        return handle.fields(key).get()

    def upload_file(self, item:Dixel):
        # See <https://wiki.xnat.org/display/XKB/Uploading+Zip+Archives+to+XNAT>

        project_id = item.meta.get("ProjectID")
        subject_id = item.tags.get("PatientID")  # This is label, not subject id?
        study_id = item.tags.get("AccessionNumber")

        params = {'overwrite': 'delete',
                  'project': project_id,
                  'subject': subject_id,
                  'session': study_id}

        # dest = '/archive/projects/%s/subjects/%s/experiments/%s' %
        #   (item.subject.project_id, item.subject.subject_id, item.study_id)
        # params.update({'dest': dest})

        if item.level < Dlv.INSTANCES:
            headers = {'content-type': 'application/zip'}
        else:
            headers = {'content-type': 'application/dicom'}
        self.gateway.send('data/services/import', params=params, headers=headers, data=item.data)

        # TODO: Need to check for upload errors when a duplicate study is pushed.

    def put(self, item: Dixel, project_id=None, subject_id=None, study_id=None):

        project_id = item.meta.get("ProjectID") or project_id
        subject_id = item.tags.get("PatientID") or subject_id
        study_id = item.tags.get("AccessionNumber") or study_id
        handle, lvl = self.select_item(project_id, subject_id, study_id)

        if not handle.get():
            handle.insert()

        for k,v in {
                    "Label": subject_id,
                    "Gender": item.tags["PatientSex"],
                    "Age": item.tags["PatientAge"]
                    }:
            handle.fields(k).set(v)

        if item.file:
            self.upload_file(item)

    def putm(self, item: Dixel, project_id=None, subject_id=None, study_id=None,
                   key=None, value=None ):

        project_id = item.meta.get("ProjectID") or project_id
        subject_id = item.tags.get("PatientID") or subject_id
        study_id = item.tags.get("AccessionNumber") or study_id
        handle, lvl = self.select_item(project_id, subject_id, study_id)

        handle.fields(key).set(value)

    def delete(self, item: Dixel, project_id=None, subject_id=None, study_id=None):

        project_id = item.meta.get("ProjectID") or project_id
        subject_id = item.tags.get("PatientID") or subject_id
        study_id = item.tags.get("AccessionNumber") or study_id
        handle, lvl = self.select_item(project_id, subject_id, study_id)

        handle.delete(params={"remove_files": True})


# class Dummy:
#
#     jsession = attr.ib(type=str, init=False)
#     @jsession.default
#     def set_jsession(self):
#         # Intialize the XNAT session
#         jsession_key = self.session.do_post('data/JSESSION')
#         self.gateway.headers.update({'JSESSIONID': jsession_key})
#         self.gateway.params.update({'format': 'json'})
#
#     def __del__(self):
#         # Close the XNAT session cleanly
#         self.gateway.do_delete('data/JSESSION')
#
#
# def xnat_bulk_edit(sheet_fn, project_id, xnat):
#     # Example of bulk editing from spreadsheet
#
#     logger = logging.getLogger(xnat_bulk_edit.__name__)
#
#     import csv
#     with open(sheet_fn, 'rbU') as csvfile:
#         propreader = csv.reader(csvfile)
#         propreader.next()
#         for row in propreader:
#             logger.info(', '.join(row))
#             subject_id = row[0]
#             new_subject_id = '{num:04d}'.format(num=int(subject_id))
#             logger.info(new_subject_id)
#
#             params = {'gender': row[1],
#                       'age': row[2],
#                       'src': row[3],
#                       'label': new_subject_id}
#             xnat.putm(None, project_id=project_id, subject_id=subject_id, params=params)
#
#
# def bulk_age_deduction():
#
#     logger = logging.getLogger(test_xnat.__name__)
#
#     s = source.subject_from_id('UOCA0008A', project_id='ava')
#     r = source.do_get('data/services/dicomdump?src=/archive/projects', s.project_id, 'subjects', s.subject_id, 'experiments', 'UOCA0008A&field=PatientAge', params={'field1': 'PatientAge', 'field': 'StudyDate'})
#
#
# def bulk_upload():
#
#     logger = logging.getLogger(test_xnat.__name__)
#
#     from tithonus import read_yaml
#     repos = read_yaml('repos.yaml')
#
#     source = Interface.factory('xnat-dev', repos)
#
#     from glob import glob
#     worklist = glob('/Users/derek/Data/hydrocephalus_dicom/*.zip')
#
#     for fn in worklist[1:]:
#         source.upload_archive(None, fn, project_id='ava')
#
# import re
# from glob import glob
# from datetime import datetime
#
#
# def deduce_yob(date_str, age_str, fmt='%Y%m%d'):
#     logger = logging.getLogger(deduce_yob.__name__)
#     age = int(re.search(r'\d+', age_str).group())
#     date = datetime.strptime(date_str, fmt).date()
#     return date.year-age
#
#
# def bulk_folder_upload():
#
#     logger = logging.getLogger(bulk_folder_upload.__name__)
#
#     from tithonus import read_yaml
#     repos = read_yaml('repos.yaml')
#
#     source = Interface.factory('xnat-dev', repos)
#
#     source.all_studies()
#
#     base_dir = '/Users/derek/Data/ATACH_I'
#     subject_worklist = glob('%s/*' % base_dir)
#     logger.info(subject_worklist)
#
#     i = 0
#
#     for subject_dir in subject_worklist:
#         subsubject_worklist = glob('%s/*' % subject_dir)
#         for subsubject_dir in subsubject_worklist:
#             study_worklist = glob('%s/*' % subsubject_dir)
#             #logger.info(study_worklist)
#             for study_dir in study_worklist:
#
#                 i = i+1
#
#                 #logger.info(study_dir)
#                 if 'scene' in study_dir.lower(): continue
#
#                 # get a dcm file to figure out the subject name, study id, and session type...
#                 session_worklist = glob('%s/*' % study_dir)
#                 session_dir = session_worklist[0]
#                 instance_worklist = glob('%s/*' % session_dir)
#                 instance_file = instance_worklist[0]
#
#                 ds = dicom.read_file(instance_file)
#
#                 #logger.info(ds)
#
#                 orig_subject_id = ds.PatientID
#                 num = int(re.search(r'\d+', orig_subject_id).group())
#                 suffix_res = re.search(r'[A-Za-z]+', orig_subject_id)
#
#                 if suffix_res:
#                     suffix = suffix_res.group().upper()
#                     if suffix == 'TIER':
#                         # Special case for silly ATACH mis-labelling
#                         if orig_subject_id.endswith('1'):
#                             suffix = 'T1'
#                         elif orig_subject_id.endswith('2'):
#                             num = 172
#                             suffix = 'T2'
#                 else:
#                     suffix = ''
#
#                 subject_id = '{num:04d}{suffix}'.format(num=int(num), suffix=str(suffix))
#
#                 study_id = ds.AccessionNumber
#
#                 study_date_str = ds.StudyDate
#                 age_str = ds.get('PatientsAge')
#
#                 if study_date_str and age_str:
#                     yob = deduce_yob(study_date_str, age_str)
#                 else:
#                     yob = None
#
#                 logger.info('%s : %s : %s' % (subject_id, study_id, yob))
#
#                 if i<=1:
#                     continue
#
#                 # source.upload_archive(None, study_dir, project_id='atach3d', study_id=study_id, subject_id=subject_id)
#                 source.upload_archive(None, 'tmp.zip', project_id='atach3d', study_id=study_id, subject_id=subject_id)
#                 if yob:
#                     source.do_put('data/archive/projects/atach3d/subjects', subject_id, params={'yob': yob})
#
#     s = source.subject_from_id('my_patient2', 'mtp01')
#     source.do_get('data/archive/projects/mtp01/subjects/my_patient2', params={'format': 'json', 'yob': '1971'})
#
#     t = DicomStudy(subject_id='my_patient3',
#                    project_id='mtp01')
#     source.upload_archive(t, 'tcia_tmp_archive1.zip')
#
#     logger.info(s)
#
#     pass
#

