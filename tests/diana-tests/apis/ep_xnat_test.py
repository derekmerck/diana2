from diana.apis import Xnat
from datetime import datetime
from hashlib import sha1
from pprint import pprint, pformat
import pytest

from diana.apis import DcmDir
from diana.dixel import Dixel, DixelView as Dv
from utils import find_resource


@pytest.mark.skip(reason="No xnat fixture")
def test_upload_file():
    dicom_dir = find_resource("resources/dcm")
    D = DcmDir(path=dicom_dir)
    d = D.get("IM2263", view=Dv.TAGS_FILE)


@pytest.mark.skip(reason="No xnat fixture")
def test_query_at_levels():

    _suffix = sha1(datetime.now().isoformat().encode('utf8')).hexdigest()[0:8]
    project_id = f"project-{_suffix}"
    subject_id = f"subject-{_suffix}"
    study_id   = f"study-{_suffix}"

    X = Xnat(port=8081)

    X.put(project_id=project_id)
    project = X.get(project_id=project_id)
    pprint(project)

    assert project["@ID"] == project_id

    X.put(project_id=project_id, subject_id=subject_id)
    subject = X.get(project_id=project_id, subject_id=subject_id)
    pprint(subject)

    assert subject["@label"] == subject_id

    X.put(project_id=project_id, subject_id=subject_id, study_id=study_id)
    study = X.get(project_id=project_id, subject_id=subject_id, study_id=study_id)
    pprint(study)

    assert study["@label"] == study_id


@pytest.mark.skip(reason="No xnat fixture")
def test_create_destroy_projects():

    _suffix = sha1(datetime.now().isoformat().encode('utf8')).hexdigest()[0:8]
    project_id = f"project-{_suffix}"

    X = Xnat(port=8081)

    for proj in X.projects():
        X.delete(proj._urn)

    projects = X.projects()
    print(f"Empty: {projects}")
    assert not projects

    print(f"Name: {project_id}")
    X.put(project_id=project_id)

    projects = X.projects()
    print(f"1 Proj: {projects}")
    assert len(projects) > 0

    X.delete(project_id=project_id)
    projects = X.projects()
    print(f"Empty: {project_id}")

    assert not projects


if __name__ == "__main__":

    test_upload_file()
