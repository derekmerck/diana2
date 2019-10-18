import ast
import click
from datetime import datetime
import os
import glob
import pydicom
import shutil
import signal
import slack
import subprocess
import time
import zipfile


@click.command(short_help="Extend images to an AI analytics package")
@click.argument('ml', type=click.STRING)
@click.option('--anonymize', '-a', is_flag=True, default=False)
@click.pass_context
def extend(ctx,
           ml,
           anonymize):
    """Examples:
    $ diana-cli extend bone_age
    """
    click.echo(click.style('Beginning AI analytics extension', underline=True, bold=True))
    try:
        sl_bot_client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])
        ba_channels = ["CM2BV81DX", "CLHKN3W3V"]
        bb_channels = ["GP57V327Q"]
        p_slack_rtm = subprocess.Popen("python /opt/diana/package/diana/daemons/slack_rtm.py {}".format(ml), shell=True, stdout=subprocess.PIPE)

        if ml == "bone_age":
            rt = "write_series_{}".format(ml)
        elif ml == "brain_bleed":
            rt = "write_series_{}".format(ml)
        else:
            raise NotImplementedError
        p_watch = subprocess.Popen("diana-cli watch -r {} radarch None".format(rt), shell=True, stdout=subprocess.PIPE)
        if not os.path.isfile("/diana_direct/{}/{}_scores.txt".format(ml, ml)):
            open("/diana_direct/{}/{}_scores.txt".format(ml, ml), 'a').close()

        while True:
            time.sleep(3)  # give json time to finish writing
            while not os.path.isfile("/diana_direct/{}/{}_results.json".format(ml, ml)):
                time.sleep(5)
            print("Query {}".format(datetime.now()))
            with open("/diana_direct/{}/{}_results.json".format(ml, ml), 'r') as data_file:
                accession_nums = parse_results(data_file, ml)

            if os.path.isfile("/diana_direct/{}/{}_slack_an.txt".format(ml, ml)):
                with open("/diana_direct/{}/{}_slack_an.txt".format(ml, ml)) as f:
                    accession_nums = [f.read().strip()]
                os.remove("/diana_direct/{}/{}_slack_an.txt".format(ml, ml))
                with open("/diana_direct/{}/{}.studies.txt".format(ml, ml), 'a+') as f:
                    for an in accession_nums:
                        f.write(an)

            # Validating second half of pipeline
            # accession_nums = [53144722]

            if len(accession_nums) == 0:
                continue
            os.remove("/diana_direct/{}/{}_results.json".format(ml, ml))

            if os.path.isfile("diana_direct/{}/{}.studies.txt".format(ml, ml)):
                os.remove("/diana_direct/{}/{}.studies.txt".format(ml, ml))
            if os.path.isfile("/diana_direct/{}/{}.key.csv".format(ml, ml)):
                os.remove("/diana_direct/{}/{}.key.csv".format(ml, ml))
            p_collect = subprocess.Popen("diana-cli collect {} /diana_direct/{} sticky_bridge radarch".format(ml, ml), shell=True)
            p_collect.wait()
            time.sleep(10)
            p_collect = subprocess.Popen("diana-cli collect {} /diana_direct/{} sticky_bridge radarch".format(ml, ml), shell=True)
            p_collect.wait()

            for i, an in enumerate(accession_nums):
                print("Processing unique a/n: {}".format(an))

                if not os.path.isdir("/diana_direct/{}/data/{}_process".format(ml, an)):
                    os.rename("/diana_direct/{}/data/{}".format(ml, an), "/diana_direct/{}/data/{}.zip".format(ml, an))
                    with zipfile.ZipFile("/diana_direct/{}/data/{}.zip".format(ml, an), 'r') as zip_ref:
                        zip_ref.extractall("/diana_direct/{}/data/{}_process".format(ml, an))
                    os.remove("/diana_direct/{}/data/{}.zip".format(ml, an))

                if ml == "bone_age":
                    subdirs = get_subdirectories("/diana_direct/{}/data/{}_process".format(ml, an))
                    for fn in subdirs:
                        if "{}".format(an) in fn:
                            dcmdir_name = fn
                            break
                    p_predict = subprocess.Popen("python3 predict.py '{}'".format(dcmdir_name), shell=True, cwd="/diana_direct/{}/package/src/".format(ml))
                    p_predict.wait()

                    with open("/opt/diana/{}_temp_predict".format(ml)) as f:
                        pred_bone_age = f.read()
                    with open("/diana_direct/{}/{}_scores.txt".format(ml, ml), "a+") as f:
                        f.write("{}, {}\n".format(an, pred_bone_age))
                elif ml == "brain_bleed":
                    files = [f for f in glob.glob("/diana_direct/{}/data/{}_process/".format(ml, an) + "**/*.dcm", recursive=True)]
                    for f in files:
                        temp_dcm = pydicom.dcmread(f)
                        if temp_dcm.SeriesDescription.lower() in ["axial brain reformat", "axial nc brain reformat", "nc axial brain reformat", "thick nc brain volume"]:
                            dcmdir_name = os.path.dirname(f)
                            break

                    p_predict = subprocess.Popen("python3 run.py '{}'".format(dcmdir_name), shell=True, cwd="/diana_direct/{}/halibut-dm/".format(ml))
                    p_predict.wait()

                    os.rename("/diana_direct/{}/data/output.npy".format(ml), "/diana_direct/{}/data/{}_output.npy".format(ml, an))

                    with open("/opt/diana/{}_temp_predict".format(ml)) as f:
                        pred_brain_bleed = f.readlines()
                    pred_brain_bleed = [_.strip() for _ in pred_brain_bleed]
                    with open("/diana_direct/{}/{}_scores.txt".format(ml, ml), "a+") as f:
                        f.write("{}, {}, {}, {}\n".format(an, pred_brain_bleed[0], pred_brain_bleed[1], pred_brain_bleed[2]))
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
                shutil.rmtree("/diana_direct/{}/data/{}_process".format(ml, an))

            os.remove("/diana_direct/{}/{}.studies.txt".format(ml, ml))
            time.sleep(2)  # slightly wait for ObservableProxiedDicom polling_interval
    except (KeyboardInterrupt, FileNotFoundError, KeyError, AssertionError) as e:
        try:
            p_slack_rtm.send_signal(signal.SIGINT)
            p_watch.send_signal(signal.SIGINT)
            p_collect.send_signal(signal.SIGINT)
            p_predict.send_signal(signal.SIGINT)
        except UnboundLocalError:
            pass
        if type(e) is FileNotFoundError:
            print("Excepted error: {}".format(e))
        if type(e) is KeyError:
            print("Key Error: {}".format(e))
        if type(e) is AssertionError:
            print("Slack Error: {}".format(e))


def parse_results(json_lines, ml):
    accession_nums = []
    for line in json_lines:
        entry = ast.literal_eval(line)
        study_desc = entry['StudyDescription'].lower()
        series_desc = entry['SeriesDescription'].lower()
        if ml == "bone_age" and ('x-ray' not in study_desc or 'bone' not in study_desc or 'age' not in study_desc):
            continue
        elif ml == "bone_age":
            print("Found X-Ray for Bone Age Study...")

        if ml == "brain_bleed" and (study_desc not in ["ct brain wo iv contrast", "ct brain c-spine wo iv contrast", "ct brain face wo iv contrast",
                                                       "ct brain face c-spine wo iv contrast", "ct brain acute stroke", "ct panscan w iv contrast",
                                                       "ct panscan with cta neck w iv contrast", "ct panscan face and cta neck w iv contrast"]):
            continue
        elif ml == "brain_bleed" and (series_desc in ["axial brain reformat", "axial nc brain reformat", "nc axial brain reformat", "thick nc brain volume"]):
            print("Found head CT...")
        elif ml == "brain_bleed":
            continue

        with open("/diana_direct/{}/{}.studies.txt".format(ml, ml), 'a+') as f:
            if entry['AccessionNumber'] in accession_nums:
                print("...duplicate a/n")
                continue

            with open("/diana_direct/{}/{}_scores.txt".format(ml, ml)) as score_file:
                if str(entry['AccessionNumber']) in score_file.read():
                    print("...duplicate a/n.")
                    continue
            f.write(entry['AccessionNumber'] + "\n")
            accession_nums.append(entry['AccessionNumber'])
    return accession_nums


# def get_immediate_subdirectories(a_dir):
#     return [name for name in os.listdir(a_dir)
#             if os.path.isdir(os.path.join(a_dir, name))]


def get_subdirectories(a_dir):
    return [f.path for f in os.scandir(a_dir) if f.is_dir()]
