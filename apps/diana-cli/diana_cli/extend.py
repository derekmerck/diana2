import ast
import click
from datetime import datetime
import glob
import os
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
        p_slack_rtm = subprocess.Popen("python /opt/diana/package/diana/daemons/slack_rtm.py {}".format(ml), shell=True, stdout=subprocess.PIPE)
        p_watch = subprocess.Popen("diana-cli watch -r write_studies radarch None", shell=True, stdout=subprocess.PIPE)
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

                # Post to Slack
                # sl_msg_response = sl_bot_client.chat_postMessage(
                #     channel="GLU6LQL86",
                #     text="Accession Number: {},\n".format("XXXX" + an[-4:]) +
                #          "Bone Age Prediction (months): {}".format(pred_bone_age)
                # )
                # try:
                #     assert(sl_msg_response["ok"])
                # except AssertionError:
                #     print("Error in Slack message post")

                # Using image thumb from bone age predictor instead
                # ba_image = glob.glob(dcmdir_name+"/**/*.dcm", recursive=True)[0]
                # p_gdcm = subprocess.Popen("python3 /opt/diana/package/diana/utils/gdcmpdcm.py '{}' {}".format(ba_image, an), shell=True)
                # p_gdcm.wait()

                for ba_channel in ba_channels:
                    sl_fiup_response = sl_bot_client.files_upload(
                        channels=ba_channel,  # WARNING: check param spelling in updates
                        file="/opt/diana/ba_thumb.png",
                        initial_comment="Accession Number: {},\n".format("XXXX" + an[-4:]) +
                             "Bone Age Prediction (months): {}".format(pred_bone_age)
                    )
                    try:
                        assert(sl_fiup_response["ok"])
                    except AssertionError:
                        print("Error in Slack fiup")

            os.remove("/diana_direct/{}/{}.studies.txt".format(ml, ml))
            time.sleep(2)  # slightly wait for ObservableProxiedDicom polling_interval
    except (KeyboardInterrupt, FileNotFoundError) as e:
        try:
            p_slack_rtm.send_signal(signal.SIGINT)
            p_watch.send_signal(signal.SIGINT)
            p_collect.send_signal(signal.SIGINT)
            p_predict.send_signal(signal.SIGINT)
            # p_gdcm.send_signal(signal.SIGINT)
        except UnboundLocalError:
            pass
        if type(e) is FileNotFoundError:
            print("Excepted error: {}".format(e))


def parse_results(json_lines, ml):
    accession_nums = []
    for line in json_lines:
        entry = ast.literal_eval(line)
        study_desc = entry['StudyDescription'].lower()
        if ml == "bone_age" and ('x-ray' not in study_desc or 'bone' not in study_desc or 'age' not in study_desc):
            continue
        else:
            print("Found X-Ray for Bone Age Study...")
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
