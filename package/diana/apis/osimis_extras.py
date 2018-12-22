import logging
from typing import Union
from . import Orthanc
from ..dixel import Dixel
from ..utils.dicom import DicomLevel


def get_annotation(source: Orthanc, study: Dixel) -> Union[dict, None]:
    """
    Method to summarize collections of Osimis-style ROI metadata and
    monkey-patch for diana.apis.Orthanc

    Considered implementing this as an annotation "view" for Orthanc.get,
    but it did not need to return a dixel as I was using it. So monkey-patching
    seemed easier for a one-off application.

    >>> from diana.apis import Orthanc, osimis_extras
    >>> o = Orthanc()
    >>> a = o.get_annotation(my_study)

    """

    try:
        resource = "studies/{}/attachments/9999/data".format(study.oid())
        ret = source.gateway._get(resource)

    except:
        logger = logging.getLogger("Osimis")
        logger.warning("No annotations to retrieve")
        return

    study_annotations = {
        'AccessionNumber': study.meta["AccessionNumber"],
        'StudyInstanceUID': study.meta["StudyInstanceUID"],
        'Annotations': []
    }

    # logging.debug( pprint.pformat(ret) )

    for k, v in ret.items():
        if not v:
            # Sometimes just an empty dict
            continue

        oid = k.split(":")[0]  # format is oid:0, presumably to support multiple users

        instance = source.get(oid, level=DicomLevel.INSTANCES)

        # logging.debug( pprint.pformat(instance.meta) )

        for data in ret[k]['ellipticalRoi']['data']:
            annotation = {
                'ImagePositionPatient': instance.meta['ImagePositionPatient'],
                'SOPInstanceUID': instance.meta['SOPInstanceUID'],
                'SeriesInstanceUID': instance.meta['SeriesInstanceUID'],
                "ROIStart": (
                    data['handles']['start']['x'],
                    data['handles']['start']['y']
                ),
                "ROIEnd": (
                    data['handles']['end']['x'],
                    data['handles']['end']['y']
                ),
                "ROIImageSize": (
                    data['imageResolution']['width'],
                    data['imageResolution']['height']
                )
            }

            # logging.debug( pprint.pformat(ret[k]['ellipticalRoi']) )
            study_annotations['Annotations'].append(annotation)

    # logging.debug( pprint.pformat(study_annotations) )
    return study_annotations


# Monkey-patch
Orthanc.get_annotation = get_annotation

