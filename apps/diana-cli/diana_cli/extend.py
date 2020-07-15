import ast
import click
from datetime import datetime
import os
import glob
import numpy as np
import pandas as pd
import pickle
import pydicom
import shutil
import signal
import slack
import subprocess
import time
import zipfile

# Selective querying
import logging
from diana.utils.endpoint import Serializable
from diana.utils.dicom import DicomLevel
from diana.dixel import Dixel, DixelView
from diana.utils.gateways.exceptions import GatewayConnectionError
from diana.apis import DcmDir, Orthanc
logging.basicConfig(filename='/opt/diana/debug.log', level=logging.DEBUG)

# Globals
ICH_STUDY_DESCRIPTIONS = ["ct brain wo iv contrast", "ct brain c-spine wo iv contrast", "ct brain face wo iv contrast",
                          "ct brain face c-spine wo iv contrast", "ct brain acute stroke", "ct panscan w iv contrast",
                          "ct panscan with cta neck w iv contrast", "ct panscan face and cta neck w iv contrast", "cta elvo head and neck",
                          "cta brain and neck w wo iv contrast", "cta brain w wo iv contrast", "ct elvo w panscan",
                          "ct elvo w dissection", "ct elvo w panscan and cta aorta bilat runoff", "ct elvo w c spine"]
ICH_SERIES_DESCRIPTIONS = ["axial brain reformat", "axial nc brain reformat", "nc axial brain reformat", "thick nc brain volume"]
ICH_THRESHOLD = 57.6

ELVO_STUDY_DESCRIPTIONS = ["cta elvo head and neck", "ct elvo w panscan", "ct elvo w dissection",
                           "ct elvo w panscan and cta aorta bilat runoff", "ct elvo w c spine"]
ELVO_SERIES_DESCRIPTIONS = [""]


@click.command(short_help="Extend images to an AI analytics package")
@click.argument('proj_path', type=click.STRING)
@click.argument('ml', type=click.STRING)
@click.option('--anonymize', '-a', is_flag=True, default=False)
@click.pass_context
def extend(ctx,
           proj_path,
           ml,
           anonymize):
    """Examples:
    $ diana-cli extend /diana_direct/elvos elvos
    """
    click.echo(click.style('Beginning AI analytics extension', underline=True, bold=True))
    try:
        sub_processes = []
        if not os.path.isdir(proj_path + "/data"):
            os.mkdir(proj_path + "/data")
        data_dir = DcmDir(path=proj_path + "/data", subpath_width=2)
        services = ctx.obj.get('services')
        PACS_Orthanc = Serializable.Factory.create(**services.get("sticky_bridge"))

        sl_bot_client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])
        ba_channels = ["CM2BV81DX", "CLHKN3W3V"]
        bb_channels = ["GP57V327Q", "GPJ16UN07"]
        el_channels = ["G016ZT9TZTL"]  # , "G016T5RLR9C"]
        p_slack_rtm = subprocess.Popen("python /opt/diana/package/diana/daemons/slack_rtm.py {} {}".format(proj_path, ml), shell=True, stdout=subprocess.PIPE)
        sub_processes.append(p_slack_rtm)

        rt = "write_series_AI"
        p_watch = subprocess.Popen("diana-cli watch -r {} radarch None {}".format(rt, proj_path), shell=True, stdout=subprocess.PIPE)
        sub_processes.append(p_watch)
        if not os.path.isfile("{}/{}_scores.txt".format(proj_path, ml)):
            open("{}/{}_scores.txt".format(proj_path, ml), 'a').close()

        clear_counter = 0
        while True:
            with open('/opt/diana/debug.log', 'w'):
                pass
            time.sleep(3)  # give json time to finish writing
            while not os.path.isfile("{}/q_results.json".format(proj_path)):
                time.sleep(3)
                logging.debug("Slept while waiting for json to finish writing")
            print("Query {}".format(datetime.now()))
            with open("{}/q_results.json".format(proj_path), 'r') as data_file:
                accession_nums = parse_results(data_file, proj_path, ml)

            if os.path.isfile("{}/{}_slack_an.txt".format(proj_path, ml)):
                with open("{}/{}_slack_an.txt".format(proj_path, ml)) as f:
                    accession_nums = [f.read().strip()]
                os.remove("{}/{}_slack_an.txt".format(proj_path, ml))

            # FOR TESTING PURPOSES: manual injection of accession #
            accession_nums = [53835704]

            if os.path.isfile("{}/{}.studies.txt".format(proj_path, ml)):
                os.remove("{}/{}.studies.txt".format(proj_path, ml))
            with open("{}/{}.studies.txt".format(proj_path, ml), 'a+') as f:
                for an in accession_nums:
                    f.write(str(an) + "\n")

            if len(accession_nums) == 0:
                clear_counter += 1
                if clear_counter > 1200:
                    open("{}/q_results.json".format(proj_path), 'w').close()
                    clear_counter = 0
                continue
            os.remove("{}/q_results.json".format(proj_path))

            if os.path.isfile("{}/{}.key.csv".format(proj_path, ml)):
                os.remove("{}/{}.key.csv".format(proj_path, ml))

            if ml == "bone_age" or ml == "elvos":
                p_collect = subprocess.Popen("diana-cli collect {} {} sticky_bridge radarch".format(ml, proj_path), shell=True)
                p_collect.wait()
                time.sleep(10)
                p_collect = subprocess.Popen("diana-cli collect {} {} sticky_bridge radarch".format(ml, proj_path), shell=True)
                p_collect.wait()
            elif ml == "brain_bleed":
                pass  # selective filtering/pulling below
            else:
                raise NotImplementedError

            for i, an in enumerate(accession_nums):
                print("Processing unique a/n: {}".format(an))
                logging.debug("Processing unique a/n: {}".format(an))
                if ml == "brain_bleed":
                    level = DicomLevel.from_label("series")
                    query = {"AccessionNumber": f"{an}",
                             "SeriesDescription": ""}
                    if hasattr(PACS_Orthanc, "rfind"):
                        logging.debug("rfind activated")
                        result = PACS_Orthanc.rfind(query, "radarch", level, retrieve=True)
                        time.sleep(10)
                        result = PACS_Orthanc.rfind(query, "radarch", level, retrieve=True)
                    else:
                        logging.debug("regular find")
                        result = PACS_Orthanc.find(query, level, retrieve=True)  # should this be True?

                    for d in result:
                        if "SeriesDescription" not in d or d['SeriesDescription'] not in ICH_SERIES_DESCRIPTIONS:
                            continue
                        # really just need oid, but oid automatically put together in Dixel class
                        dixel = Dixel.from_orthanc(meta={}, tags=d, level=level)
                        try:
                            dcm_image = PACS_Orthanc.get(dixel, level=level, view=DixelView.FILE)
                        except FileNotFoundError as e:
                            try:
                                dcm_image = PACS_Orthanc.get(dixel, level=level, view=DixelView.FILE)
                            except FileNotFoundError as e2:
                                continue
                                logging.error(e2)
                            logging.error(e)
                        data_dir.put(dcm_image)
                        try:
                            PACS_Orthanc.delete(dixel)
                        except GatewayConnectionError as e:
                            logging.error("Failed to delete dixel")
                            logging.error(e)

                if not os.path.isdir("{}/data/{}_process".format(proj_path, an)):
                    os.rename("{}/data/{}".format(proj_path, an), "{}/data/{}.zip".format(proj_path, an))
                    with zipfile.ZipFile("{}/data/{}.zip".format(proj_path, an), 'r') as zip_ref:
                        zip_ref.extractall("{}/data/{}_process".format(proj_path, an))
                    os.remove("{}/data/{}.zip".format(proj_path, an))

                dcmdir_name = None
                dcmdir_name = get_dcmdir_name(ml, proj_path, an)
                if dcmdir_name is None:
                    print("dcmdir_name is None")
                    continue
                if ml == "bone_age":
                    p_predict = subprocess.Popen("python3 predict.py '{}'".format(dcmdir_name), shell=True, cwd="{}/package/src/".format(proj_path))
                    sub_processes.append(p_predict)
                    p_predict.wait()

                    with open("/opt/diana/{}_temp_predict".format(ml)) as f:
                        pred_bone_age = f.read()
                    with open("{}/{}_scores.txt".format(proj_path, ml), "a+") as f:
                        f.write("{}, {}, {}\n".format(an, str(datetime.now()), pred_bone_age))
                elif ml == "brain_bleed":
                    # Filter out non-ER cases by StationName
                    f = dcmdir_name(1)  # TODO: check if overwritten after next line
                    dcmdir_name = dcmdir_name(0)
                    s = pydicom.dcmread(f)
                    try:
                        assert(s.StationName.lower() == "cter" or s.StationName.upper() == "CTAWP66457")
                    except (AttributeError, AssertionError):
                        print("No station name or not ER scanner")
                        shutil.rmtree("{}/data/{}_process".format(proj_path, an))
                        with open("{}/{}_scores.txt".format(proj_path, ml), "a+") as f:
                            f.write("{}, {}, -, -, NOT_ER_SCANNER\n".format(an, str(datetime.now())))
                        continue

                    p_predict = subprocess.Popen("python3 run.py '{}'".format(dcmdir_name), shell=True, cwd="{}/halibut-dm/".format(proj_path))
                    p_predict.wait()

                    os.rename("{}/data/output.npy".format(proj_path), "{}/data/{}_output.npy".format(proj_path, an))

                    with open("/opt/diana/{}_temp_predict".format(ml)) as f:
                        pred_brain_bleed = f.readlines()
                    pred_brain_bleed = [_.strip() for _ in pred_brain_bleed]
                    with open("{}/{}_scores.txt".format(proj_path, ml), "a+") as f:
                        f.write("{}, {}, {}, {}, {}\n".format(an, str(datetime.now()), pred_brain_bleed[0], pred_brain_bleed[1], pred_brain_bleed[2]))
                    if float(pred_brain_bleed[0]) < ICH_THRESHOLD:
                        print("ICH below threshold")
                        continue
                elif ml == "elvos":
                    # Series-type prediction
                    pred_csv = "{}/src/pred.csv".format(proj_path)
                    df = pd.read_csv(pred_csv)
                    for _i, _ in enumerate(dcmdir_name):
                        df.at["series"][_i] = _
                    df = df.truncate(after=_i)
                    df.to_csv(pred_csv, index=False)
                    p_predict = subprocess.Popen("python3 run.py --gpu -1 {} predict".format("{}/src/configs/predict/diana_series.yaml".format(proj_path)), shell=True, cwd="{}/src/".format(proj_path))
                    p_predict.wait()

                    with open("{}/src/predictions.pkl".format(proj_path), "rb") as f:
                        series_pred = pickle.load(f)

                    preds = []
                    for _ in series_pred['y_pred']:
                        if _ is not None:
                            preds.append(_[0][0])
                    test_csv = "{}/src/test.csv".format(proj_path)
                    df = pd.read_csv(test_csv)
                    df["series"][0] = series_pred['series'][np.argmax(preds)] + "/CT.npy"
                    df["label"][0] = 0
                    df.to_csv(test_csv, index=False)

                    images = []
                    for _ in os.listdir(series_pred['series'][np.argmax(preds)]):
                        images.append(pydicom.read_dicom(_).pixel_array)
                    images = np.asarray(images)
                    np.save("{}/src/CT-npy/CT.npy".format(proj_path), images)

                    # ELVO-type
                    votes = []
                    percents = []
                    for _ in range(3):
                        p_test = subprocess.Popen("python3 run.py --gpu -1 {} test".format("{}/src/configs/3-models/model{}.yaml".format(proj_path, _)), shell=True, cwd="{}/src/".format(proj_path))
                        p_test.wait()
                        time.sleep(0.5)
                        with open("{}/src/pred/predictions.pkl", "rb") as f:
                            model_results = pickle.load(f)
                        votes.append(np.argmax(model_results["y_pred"]))
                        percents.append(model_results["y_pred"][-1])
                    result = "No acute ELVO"
                    if votes.count(2) > 1:
                        result = "ACUTE ELVO"
                    prob = np.round(np.mean(percents) * 100., 2)

                    with open("{}/{}_scores.txt".format(proj_path, ml), "a+") as f:
                        f.write("{}, {}, {}\n".format(an, str(datetime.now()), prob))
                    # np.save("/opt/diana/{}_arr.npy".format(ml), get_3darray_from_dicom(dcmdir_name))
                else:
                    raise NotImplementedError

                if ml == "bone_age":
                    yrs = int(float(pred_bone_age) / 12)
                    months = round(float(pred_bone_age) % 12, 2)
                    for channel in ba_channels:
                        sl_fiup_response = sl_bot_client.files_upload(
                            channels=channel,  # WARNING: check param spelling in updates
                            file="/opt/diana/ba_thumb.png",
                            initial_comment="Accession Number: {},\n".format("XXXX" + an[-4:]) +
                                 "Bone Age Prediction: {} year(s) and {} month(s)".format(yrs, months)
                        )
                        assert(sl_fiup_response["ok"])
                elif ml == "brain_bleed":
                    for channel in bb_channels:
                        sl_fiup_response = sl_bot_client.files_upload(
                            channels=channel,  # WARNING: check param spelling in updates
                            file="/opt/diana/bb_thumb.png",
                            initial_comment="Accession Number: {},\n".format("XXXX" + an[-4:]) +
                            "ICH Prediction: {} - {}%".format(pred_brain_bleed[-1], pred_brain_bleed[0])
                        )
                        assert(sl_fiup_response["ok"])
                elif ml == "elvos":
                    for channel in el_channels:
                        sl_fiup_response = sl_bot_client.files_upload(
                            channels=channel,  # WARNING: check param spelling in updates
                            file="/opt/diana/el_thumb.txt",
                            initial_comment="Accession Number: {},\n".format("XXXX" + an[-4:]) +
                            "ELVO result: {} - {}%".format(result, prob)
                        )
                        assert(sl_fiup_response["ok"])
                shutil.rmtree("{}/data/{}_process".format(proj_path, an))

            # p_watch.terminate() # WARNING: this may create many many Docker container archives along w/ subsequent re-Popen...
            time.sleep(1)
            # p_watch = subprocess.Popen("diana-cli watch -r {} radarch None {}".format(rt, proj_path), shell=True, stdout=subprocess.PIPE)
    except (KeyboardInterrupt, FileNotFoundError, KeyError, AssertionError) as e:
        if type(e) is FileNotFoundError:
            print("Excepted error: {}".format(e))
        elif type(e) is KeyError:
            print("Key Error: {}".format(e))
        elif type(e) is AssertionError:
            print("Slack Error: {}".format(e))
        else:
            print("Some error: {}".format(e))

        try:
            for _ in sub_processes:
                os.killpg(os.getpgid(_.pid), signal.SIGTERM)
            # p_slack_rtm.send_signal(signal.SIGTERM)
            # p_watch.send_signal(signal.SIGTERM)
            # p_collect.send_signal(signal.SIGTERM)
            # p_predict.send_signal(signal.SIGTERM)
        except UnboundLocalError:
            print("UnboundLocalError on sending SIGTERM signals")  # TODO: address
            pass


def parse_results(json_lines, proj_path, ml):
    accession_nums = []
    for line in json_lines:
        entry = ast.literal_eval(line)
        study_desc = entry['StudyDescription'].lower()
        series_desc = entry['SeriesDescription'].lower()

        if ml == "bone_age" and ('x-ray' not in study_desc or 'bone' not in study_desc or 'age' not in study_desc):
            continue
        elif ml == "bone_age":
            print("Found X-Ray for Bone Age Study...")

        if ml == "brain_bleed" and (study_desc not in ICH_STUDY_DESCRIPTIONS):
            continue
        elif ml == "brain_bleed" and (series_desc in ICH_SERIES_DESCRIPTIONS):
            print("Found head CT...")
        elif ml == "brain_bleed":
            continue

        if ml == "elvos" and (study_desc not in ELVO_STUDY_DESCRIPTIONS):
            continue
        elif ml == "elvos" and (series_desc in ELVO_SERIES_DESCRIPTIONS):
            print("Found ELVO study...")
        elif ml == "elvos":
            continue

        with open("{}/{}.studies.txt".format(proj_path, ml), 'a+') as f:
            if entry['AccessionNumber'] in accession_nums:
                print("...duplicate a/n")
                continue

            with open("{}/{}_scores.txt".format(proj_path, ml)) as score_file:
                if str(entry['AccessionNumber']) in score_file.read():
                    print("...duplicate a/n")
                    continue
            f.write(entry['AccessionNumber'] + "\n")
            accession_nums.append(entry['AccessionNumber'])
    return accession_nums


def get_dcmdir_name(ml, proj_path, an):
    dcmdir_name = None
    if ml == "bone_age":
        subdirs = get_subdirectories("{}/data/{}_process".format(proj_path, an))
        for fn in subdirs:
            if "{}".format(an) in fn:
                dcmdir_name = fn
                break
    elif ml == "brain_bleed":
        files = [f for f in glob.glob("{}/data/{}_process/".format(proj_path, an) + "**/*.dcm", recursive=True)]
        for f in files:
            temp_dcm = pydicom.dcmread(f)
            if temp_dcm.SeriesDescription.lower() in ICH_SERIES_DESCRIPTIONS:
                dcmdir_name = os.path.dirname(f)
                break
        return dcmdir_name, f
    elif ml == "elvos":
        subdirs = get_all_subdirectories("{}/data/{}_process".format(proj_path, an))
        for fn in subdirs:
            if folder_count(fn) > 1:
                dcmdir_name = get_subdirectories(fn)
                break

    return dcmdir_name


def get_all_subdirectories(a_dir):
    return [_[0] for _ in os.walk(a_dir)]


def get_subdirectories(a_dir):
    return [f.path for f in os.scandir(a_dir) if f.is_dir()]


def folder_count(a_dir):
    return len([f for f in os.scandir(a_dir) if f.is_dir()])


def get_2dslice_from_dicom(dcmfile):
    dcm = pydicom.dcmread(dcmfile)
    array = dcm.pixel_array
    array = array * int(dcm.RescaleSlope)
    array = array + int(dcm.RescaleIntercept)
    array = array.astype('float32')
    z_pos = dcm.ImagePositionPatient[2]
    return array, z_pos


def get_3darray_from_dicom(dcmfolder):
    # Assumes everything is DICOM
    dcmfiles = glob.glob(os.path.join(dcmfolder, '*'))
    array = [get_2dslice_from_dicom(_) for _ in dcmfiles]
    z_pos = np.asarray([_[1] for _ in array])
    array = np.asarray([_[0] for _ in array])
    # Now, rearrange slices by z-position
    order = np.argsort(z_pos)
    array = array[order]
    # Now, we need to pad empty slices on top/bottom to create 2Dc stacked images
    # empty = np.zeros((array.shape[1], array.shape[2]))
    empty = np.zeros((1, array.shape[1], array.shape[2]))
    empty[:] = np.min(array)
    array = np.vstack((empty, array, empty))
    return array
