# Reference: <https://pyscience.wordpress.com/2015/02/15/python-access-to-the-cancer-imaging-archive-tcia-through-a-rest-api/>

import logging
import os

from Interface import Interface
from Polynym import DicomSeries, DicomStudy, DicomSubject

from XNATInterface import deduce_yob

class Tcia(Interface):

    # def do_get(self, *url, **kwargs):
    #     params = kwargs.get('params')
    #     if params:
    #         params['api_key'] = self.api_key
    #         kwargs['params'] = params
    #     else:
    #         params = {'api_key': self.api_key}
    #         kwargs['params'] = params
    #     # self.logger.info(params)
    #     return super(TCIAInterface, self).do_get(*url, **kwargs)

    def __init__(self, **kwargs):
        super(TCIAInterface, self).__init__(**kwargs)
        self.session.params['api_key'] = self.api_key

    def series_from_id(self, series_id):
        series_info = self.find('series', series_id)
        # Sample series info:
        # [{u'SeriesDate': u'2000-01-01', u'SeriesNumber': u'1.000000', u'SeriesDescription': u'Topogram  0.6  T20s', u'Collection': u'CT COLONOGRAPHY', u'BodyPartExamined': u'COLON', u'SoftwareVersions': u'syngo CT 2005A', u'Visibility': u'1', u'ProtocolName': u'14_SUPINE_COLON', u'StudyInstanceUID': u'1.3.6.1.4.1.9328.50.4.15566', u'SeriesInstanceUID': u'1.3.6.1.4.1.9328.50.4.15567', u'ManufacturerModelName': u'Sensation 64', u'Modality': u'CT', u'ImageCount': 1, u'Manufacturer': u'SIEMENS'}]

        study_id = series_info[0]['StudyInstanceUID']
        study = self.study_from_id(study_id)
        series = DicomSeries(series_id=series_id, study=study, anonymized=True)
        series['series_id', self] = series_id
        return series

    def study_from_id(self, study_id):
        study_info = self.find('study', study_id)
        # Sample study info:
        # [{u'StudyDate': u'2000-01-01', u'StudyDescription': u'Abdomen^14_SUPINE_COLON (Adult)', u'PatientID': u'1.3.6.1.4.1.9328.50.4.0016', u'Collection': u'CT COLONOGRAPHY', u'PatientAge': u'052Y', u'PatientSex': u'F', u'StudyInstanceUID': u'1.3.6.1.4.1.9328.50.4.15566', u'PatientName': u'1.3.6.1.4.1.9328.50.4.0016', u'SeriesCount': 3}]

        subject_id = study_info[0]['PatientID']
        subject_name = study_info[0]['PatientName']
        project_id = study_info[0]['Collection']

        date_str = study_info[0]['StudyDate']
        age_str = study_info[0]['PatientAge']
        yob = deduce_yob(date_str, age_str, fmt='%Y-%m-%d')
        gender = study_info[0]['PatientSex']

        subject = DicomSubject(subject_id=subject_id,
                               subject_name=subject_name,
                               yob=yob,
                               gender=gender,
                               project_id=project_id)

        # subject = self.subject_from_id(subject_id, project_id)
        study = DicomStudy(study_id=study_id, subject=subject, anonymized=True)
        study['study_id', self] = study_id
        return study

    def subject_from_id(self, subject_id, project_id=None):
        # subject = DicomSubject(subject_id=subject_id, anonymized=True)
        # subject['subject_id', self] = subject_id
        # return subject

        # This query is unfortunately quite indirect.  For some collections (CT COLONOGRAPHY) it is also useless, as
        # the PatientID is just the PatientUID

        all_subjects_info = self.find('subject', project_id)
        # List of entries sample: {u'PatientSex': u'F', u'PatientID': u'1.3.6.1.4.1.9328.50.4.0001', u'Collection': u'CT COLONOGRAPHY', u'PatientName': u'1.3.6.1.4.1.9328.50.4.0001'}

        self.logger.debug("First entry: %s" % all_subjects_info[0])

        subject_info = {}
        for s in all_subjects_info:
            #self.logger.debug(s)
            if subject_id in s.values():
                subject_info = s
                break

        subject = DicomSubject(subject_id=subject_id, subject_name=subject_info['PatientID'], anonymized=True)
        subject['subject_id', self] = subject_id
        return subject

    def find(self, level, question, source=None):

        url = None
        params = None
        if level=='series':
            params = {'SeriesInstanceUID': question,
                      'format': 'json'}
            url = 'query/getSeries'
        elif level=='study':
            params = {'StudyInstanceUID': question,
                      'format': 'json'}
            url = 'query/getPatientStudy'
        elif level=='subject':
            params = {'Collection': question,
                      'format': 'json'}
            url = 'query/getPatient'
            # Actually returns a list of all subjects in the project
        else:
            self.logger.warn("Undefined query level!")

        return self.do_get(url, params=params)

    def download_data(self, item):
        # Only has interface for "series"
        if isinstance(item, DicomSeries):
            item.data = self.do_get('query/getImage', params={'SeriesInstanceUID': item['series_id', self]})
        else:
            self.logger.warn('TCIAInterface can only download series items')


def tcia_mirror():

    logger = logging.getLogger(tcia_tests.__name__)

    # Test TCIA Instantiate
    from tithonus import read_yaml
    repos = read_yaml('repos.yaml')

    source = Interface.factory('tcia', repos)
    target = Interface.factory('xnat-dev', repos)

    fn = '/Users/derek/Desktop/tcia-all-seriesInstanceUids1438444078500.csv'

    import csv
    with open(fn, 'rbU') as csvfile:
        seriesreader = csv.reader(csvfile)
        seriesreader.next()

        i = 0
        for row in seriesreader:
            i = i+1

            if i<=0: continue
            if i>5: break

            logger.info(', '.join(row))
            group = row[0]
            # subject_id = row[1]
            series_id = row[9]

            item = source.series_from_id(series_id)
            #source.download_data(item)

            # Change vars for XNAT
            item['collection'] = group
            item.subject.project_id = 'tcia'
            #target.upload_data(item)

            target.do_put('data/archive/projects', item.subject.project_id, 'subjects',
                          item.subject.subject_id.replace('.','_'),
                          params={'group': item['collection'],
                                  'yob': item.subject['yob'],
                                  'gender': item.subject['gender']})



    pass



def tcia_tests():
    # The TCIA interface is very slow, so uncomment to skip this one
    #raise SkipTest

    logger = logging.getLogger(tcia_tests.__name__)

    # Test TCIA Instantiate
    from tithonus import read_yaml
    repos = read_yaml('repos.yaml')

    source = Interface.factory('tcia', repos)

    # source = TCIAInterface(address='https://services.cancerimagingarchive.net/services/v3/TCIA',
    #                        api_key=os.environ['TCIA_API_KEY'])

    # Apparently API key doesn't work for NLST b/c it is a private collection
    # series = source.get_series_from_id('1.2.840.113654.2.55.4303894980888172655039251025765147023')
    # source.download_archive(series, 'nlst_tmp_archive')

    # Test TCIA Download
    series = source.get_series_from_id('1.3.6.1.4.1.9328.50.4.15567')
    source.download_archive(series, 'tcia_tmp_archive')
    assert os.path.getsize('tcia_tmp_archive.zip') == 266582
    os.remove('tcia_tmp_archive.zip')

    # Test TCIA Copy
    source.copy(series, source, 'tcia_tmp_archive')
    assert os.path.getsize('tcia_tmp_archive.zip') == 266582
    os.remove('tcia_tmp_archive.zip')


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    tcia_mirror()