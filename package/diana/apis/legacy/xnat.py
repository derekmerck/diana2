"""
Xnat 1.x DIANA interface

Xnat level   DICOM level
----------   -----------
Project      Arbitrary
Subject      Patient
Experiment   Study
Scans        Series
"""

from crud.abc import Endpoint, Serializable
from diana.dixel import Dixel
import logging
import attr
import xmltodict
from pyxnat import Interface as XnatGateway
# I originally wrote this using requests directly

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

    def get(self, project_id, subject_id=None, study_id=None) -> Dixel:
        if not subject_id:
            ret = self.gateway.select.project(project_id).get()
            data = xmltodict.parse(ret)
            return data.get("xnat:Project")
        elif not study_id:
            ret = self.gateway.select.project(project_id).subject(subject_id).get()
            data = xmltodict.parse(ret)
            return data.get("xnat:Subject")
        else:
            ret = self.gateway.select.project(project_id).subject(subject_id).\
                experiment(study_id).get()
            data = xmltodict.parse(ret)
            return data.get("xnat:MRSession")

    def put(self, project_id, subject_id=None, study_id=None):
        if not subject_id:
            self.gateway.select.project(project_id).insert()
        elif not study_id:
            self.gateway.select.project(project_id).subject(subject_id).insert()
        else:
            self.gateway.select.project(project_id).subject(subject_id).\
                experiment(study_id).insert()

    def delete(self, project_id, subject_id=None, study_id=None):
        # TODO: should pass {"remove_files": True} in params
        if not subject_id:
            self.gateway.select.project(project_id).delete()
        elif not study_id:
            self.gateway.select.project(project_id).subject(subject_id).delete()
        else:
            self.gateway.select.project(project_id).subject(subject_id).\
                experiment(study_id).delete()


class Dummy:

    jsession = attr.ib(type=str, init=False)
    @jsession.default
    def set_jsession(self):
        # Intialize the XNAT session
        jsession_key = self.session.do_post('data/JSESSION')
        self.gateway.headers.update({'JSESSIONID': jsession_key})
        self.gateway.params.update({'format': 'json'})

    def __del__(self):
        # Close the XNAT session cleanly
        self.gateway.do_delete('data/JSESSION')


    def upload_data(self, item):
        # See <https://wiki.xnat.org/display/XKB/Uploading+Zip+Archives+to+XNAT>

        if isinstance(item, DicomStudy) or isinstance(item, DicomSeries):
            params = {'overwrite': 'delete',
                      'project': item.subject.project_id}

            # dest = '/archive/projects/%s/subjects/%s/experiments/%s' % (item.subject.project_id, item.subject.subject_id, item.study_id)
            # params.update({'dest': dest})

            if item.subject.get('subject_id'):
                params.update({'subject': item.subject.subject_id})
            if item.get('study_id'):
                params.update({'session': item.study_id})

            headers = {'content-type': 'application/zip'}
            self.do_post('data/services/import', params=params, headers=headers, data=item.data)
        else:
            self.logger.warn('XNATInterface can only upload study items')

        # TODO: Need to check for upload errors when a duplicate study is pushed.


    def upload_archive(self, item, fn, **kwargs):
        # Note that we need _at least_ the project_id or it will go into the prearchive
        if item is None:
            # Make up a dummy study from the kwargs
            item = DicomStudy(**kwargs)

        self.logger.debug(item)
        super(XNATInterface, self).upload_archive(item, fn)

    # XNAT specific

    def set_study_attribute(self, study, key):
        value = study.__dict__[key]
        params = {self.var_dict[key]: value}
        self.do_put('data/archive/projects', study.subject.project_id,
                    'subjects', study.subject.subject_id[self],
                    'experiments', study.study_id[self],
                    params=params)

def xnat_bulk_edit():
    # Example of bulk editing from spreadsheet

    logger = logging.getLogger(xnat_bulk_edit.__name__)

    import csv
    with open('/Users/derek/Desktop/protect3d.variables.csv', 'rbU') as csvfile:
        propreader = csv.reader(csvfile)
        propreader.next()
        for row in propreader:
            logger.info(', '.join(row))
            subject_id = row[0]
            new_subject_id = '{num:04d}'.format(num=int(subject_id))
            logger.info(new_subject_id)

            params = {'gender': row[1],
                      #'age': row[2],
                      'src': row[3],
                      'label': new_subject_id}
            source.do_put('data/archive/projects/protect3d/subjects', subject_id, params=params)


def bulk_age_deduction():

    logger = logging.getLogger(test_xnat.__name__)

    s = source.subject_from_id('UOCA0008A', project_id='ava')
    r = source.do_get('data/services/dicomdump?src=/archive/projects', s.project_id, 'subjects', s.subject_id, 'experiments', 'UOCA0008A&field=PatientAge', params={'field1': 'PatientAge', 'field': 'StudyDate'})


def bulk_upload():

    logger = logging.getLogger(test_xnat.__name__)

    from tithonus import read_yaml
    repos = read_yaml('repos.yaml')

    source = Interface.factory('xnat-dev', repos)

    from glob import glob
    worklist = glob('/Users/derek/Data/hydrocephalus_dicom/*.zip')

    for fn in worklist[1:]:
        source.upload_archive(None, fn, project_id='ava')

import re
from glob import glob
from datetime import datetime


def deduce_yob(date_str, age_str, fmt='%Y%m%d'):
    logger = logging.getLogger(deduce_yob.__name__)
    age = int(re.search(r'\d+', age_str).group())
    date = datetime.strptime(date_str, fmt).date()
    return date.year-age


def bulk_folder_upload():

    logger = logging.getLogger(bulk_folder_upload.__name__)

    from tithonus import read_yaml
    repos = read_yaml('repos.yaml')

    source = Interface.factory('xnat-dev', repos)

    source.all_studies()

    base_dir = '/Users/derek/Data/ATACH_I'
    subject_worklist = glob('%s/*' % base_dir)
    logger.info(subject_worklist)

    i = 0

    for subject_dir in subject_worklist:
        subsubject_worklist = glob('%s/*' % subject_dir)
        for subsubject_dir in subsubject_worklist:
            study_worklist = glob('%s/*' % subsubject_dir)
            #logger.info(study_worklist)
            for study_dir in study_worklist:

                i = i+1

                #logger.info(study_dir)
                if 'scene' in study_dir.lower(): continue

                # get a dcm file to figure out the subject name, study id, and session type...
                session_worklist = glob('%s/*' % study_dir)
                session_dir = session_worklist[0]
                instance_worklist = glob('%s/*' % session_dir)
                instance_file = instance_worklist[0]

                ds = dicom.read_file(instance_file)

                #logger.info(ds)

                orig_subject_id = ds.PatientID
                num = int(re.search(r'\d+', orig_subject_id).group())
                suffix_res = re.search(r'[A-Za-z]+', orig_subject_id)

                if suffix_res:
                    suffix = suffix_res.group().upper()
                    if suffix == 'TIER':
                        # Special case for silly ATACH mis-labelling
                        if orig_subject_id.endswith('1'):
                            suffix = 'T1'
                        elif orig_subject_id.endswith('2'):
                            num = 172
                            suffix = 'T2'
                else:
                    suffix = ''

                subject_id = '{num:04d}{suffix}'.format(num=int(num), suffix=str(suffix))

                study_id = ds.AccessionNumber

                study_date_str = ds.StudyDate
                age_str = ds.get('PatientsAge')

                if study_date_str and age_str:
                    yob = deduce_yob(study_date_str, age_str)
                else:
                    yob = None

                logger.info('%s : %s : %s' % (subject_id, study_id, yob))

                if i<=1:
                    continue

                # source.upload_archive(None, study_dir, project_id='atach3d', study_id=study_id, subject_id=subject_id)
                source.upload_archive(None, 'tmp.zip', project_id='atach3d', study_id=study_id, subject_id=subject_id)
                if yob:
                    source.do_put('data/archive/projects/atach3d/subjects', subject_id, params={'yob': yob})

    s = source.subject_from_id('my_patient2', 'mtp01')
    source.do_get('data/archive/projects/mtp01/subjects/my_patient2', params={'format': 'json', 'yob': '1971'})

    t = DicomStudy(subject_id='my_patient3',
                   project_id='mtp01')
    source.upload_archive(t, 'tcia_tmp_archive1.zip')

    logger.info(s)

    pass


