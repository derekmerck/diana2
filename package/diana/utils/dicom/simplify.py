import logging
from . import parse_dicom_datetime as mk_time
from .exceptions import DicomFormatError


def handle_errors(err, ignore_errors):

    if ignore_errors:
        logger = logging.getLogger("DcmSimplify")
        logger.error(err)
        return
    else:
        raise DicomFormatError()


def parse_timestamps(tags, ignore_errors):
    """Convert times to DT objects and infer an instance dt if needed."""

    if tags.get("StudyDate"):
        tags["StudyDateTime"] = mk_time(tags.get("StudyDate"), tags.get("StudyTime"))

    if tags.get("SeriesDate"):
        tags["SeriesDateTime"] = mk_time(tags.get("SeriesDate"), tags.get("SeriesTime"))

    if not tags.get("SeriesDateTime"):
        tags["SeriesDateTime"] = tags.get("StudyDateTime")

    if not tags.get("InstanceCreationDateTime"):
        err = "No series creation time identified"
        handle_errors(err, ignore_errors)

    if tags.get("InstanceCreationDate"):
        tags["InstanceCreationDateTime"] = mk_time(tags.get("InstanceCreationDate"),
                                                   tags.get("InstanceCreationTime"))

    if not tags.get("InstanceCreationDateTime"):
        tags["InstanceCreationDateTime"] = tags.get("SeriesDateTime") or \
                                           tags.get("StudyDateTime")

    if not tags.get("InstanceCreationDateTime"):
        err = "No instance creation time identified"
        handle_errors(err, ignore_errors)

    return tags


def normalize_dose_report(tags):
    """Standardize how dose report keys and values.  Certain data is presented
    in platform-specific ways, which makes the data difficult to parse with
    Splunk"""

    try:

        # Note lowercase
        if tags.get("X-ray Radiation Dose Report"):
            tags["X-Ray Radiation Dose Report"] = tags.get("X-ray Radiation Dose Report")
            del tags["X-ray Radiation Dose Report"]

        exposures = tags["X-Ray Radiation Dose Report"]["CT Acquisition"]

        # If there is only a single exposure, the exposures are not _listed_
        # Converting to a list of 1 normalizes the code.
        if not isinstance(exposures, list):
            tags["X-Ray Radiation Dose Report"]["CT Acquisition"] = [exposures]

        for exposure in exposures:

            if "CT Dose" not in exposure:
                logger = logging.getLogger("DcmSimplify")
                logger.debug("Normalizing missing CT Dose key")
                exposure["CT Dose"] = {'Mean CTDIvol': 0}
            else:
                # logger.debug("CT Dose key already exists!")
                pass

    except:
        pass

    return tags


def impute_accession_number(tags, ignore_errors):

    if not tags.get("AccessionNumber"):
        try:
            tags["AccessionNumber"] = tags["StudyInstanceUID"]
        except KeyError:
            tags["AccessionNumber"] = "Unknown"
            handle_errors("No accession number/study uid identified", ignore_errors)

    return tags


def impute_patient_name(tags, ignore_errors):
    """Make sure that a StationName is present or introduce a sensible alternative"""
    if not tags.get("PatientName"):
        try:
            tags["PatientName"] = tags["PatientID"]
        except KeyError:
            tags["PatientName"] = "Unknown"
            handle_errors("No patient name/id identified", ignore_errors)

    return tags


def impute_station_name(tags):
    """Make sure that a StationName is present or introduce a sensible alternative"""

    if not tags.get("StationName"):
        try:
            tags["StationName"] = tags["DeviceSerialNumber"]
        except:
            try:
                tags["StationName"] = tags["X-Ray Radiation Dose Report"]["Device Observer UID"]
            except:
                tags["StationName"] = "Unknown"
                logger = logging.getLogger("DcmSimplify")
                logger.warning('No station name identified')

    return tags


def flatten_content_sequence(tags):

    data = {}

    for item in tags["ContentSequence"]:

        # logger.debug('Item = ' + pformat(item))

        try:
            key = item['ConceptNameCodeSequence'][0]['CodeMeaning']
            type_ = item['ValueType']
            value = None
        except KeyError:
            logger = logging.getLogger("DcmSimplify")
            logger.debug('No key or no type, returning')
            return

        if type_ == "TEXT":
            value = item['TextValue']
            # logger.debug('Found text value')

        elif type_ == "IMAGE":
            # "IMAGE" sometimes encodes a text UUID, sometimes a refsop
            try:
                value = item['TextValue']
            except KeyError:
                logger = logging.getLogger("DcmSimplify")
                logger.debug('No text value for "IMAGE", returning')
                return

        elif type_ == "NUM":
            value = float(item['MeasuredValueSequence'][0]['NumericValue'])
            # logger.debug('Found numeric value')
        elif type_ == 'UIDREF':
            value = item['UID']
            # logger.debug('Found uid value')
        elif type_ == 'DATETIME':
            value = mk_time(item['DateTime'])
            # logger.debug('Found date/time value')
        elif type_ == 'CODE':
            try:
                value = item['ConceptCodeSequence'][0]['CodeMeaning']
            except:
                value = "UNKNOWN"
            # logger.debug('Found coded value')
        elif type_ == "CONTAINER":
            value = flatten_content_sequence(item)
            # logger.debug('Found container - recursing')
        else:
            logger = logging.getLogger("DcmSimplify")
            logger.debug("Unknown ValueType (" + item['ValueType'] + ")")

        if data.get(key):
            # logger.debug('Key already exists (' + key + ')')
            if isinstance(data.get(key), list):
                value = data[key] + [value]
                # logger.debug('Already a list, so appending')
            else:
                value = [data[key], value]
                # logger.debug('Creating a list from previous and current')

        data[key] = value

    return data


def flatten_structured_tags(tags):

    # Parse any structured data into simplified tag structure
    if tags.get('ConceptNameCodeSequence'):
        # There is structured data in here
        key = tags['ConceptNameCodeSequence'][0]['CodeMeaning']
        value = flatten_content_sequence(tags)

        dt = mk_time(tags['ContentDate'], tags['ContentTime'])
        value['ContentDateTime'] = dt

        del(tags['ConceptNameCodeSequence'])
        del(tags['ContentSequence'])
        del(tags['ContentDate'])
        del(tags['ContentTime'])

        tags[key] = value

    return tags


def dicom_simplify(tags, ignore_errors=True):
    """
    Simplify a DICOM tag set:
      - Standardize dates and times as Python datetime objects
      - Identify a sensible creation datetime
      - Flatten and simplify ContentSequences in the manner of Orthanc's 'simplify' parameter
      - Add sensible defaults for missing station names
      - Add sensible defaults for exposure data in dose reports
    """

    # Convert timestamps to python datetimes
    tags = parse_timestamps(tags, ignore_errors)

    # Flatten content sequences
    tags = flatten_structured_tags(tags)

    # Deal with missing tags
    tags = impute_accession_number(tags, ignore_errors)
    tags = impute_patient_name(tags, ignore_errors)
    tags = impute_station_name(tags)

    # Deal with radiation exposure data
    tags = normalize_dose_report(tags)

    # logger.info(pformat(tags))

    return tags


