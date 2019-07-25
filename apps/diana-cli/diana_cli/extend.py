import click
from datetime import datetime
import json
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
        sl_client = slack.WebClient(token=os.environ['SLACK_BOT_TOKEN'])
        p_watch = subprocess.Popen("diana-cli watch -r write_studies radarch None", shell=True, stdout=subprocess.PIPE)
        if not os.path.isfile("/diana_direct/{}/{}_scores.txt".format(ml, ml)):
            open("/diana_direct/{}/{}_scores.txt".format(ml, ml), 'a').close()

        while True:
            time.sleep(5)  # give json time to finish writing
            while not os.path.isfile("/diana_direct/{}/{}_results.json".format(ml, ml)):
                time.sleep(5)
            print("Query {}".format(datetime.now()))
            with open("/diana_direct/{}/{}_results.json".format(ml, ml), 'r') as data_file:
                accession_nums = parse_results(data_file, ml)
            os.remove("/diana_direct/{}/{}_results.json".format(ml, ml))

            # Validating second half of pipeline
            # accession_nums = [53144722]

            if len(accession_nums) == 0:
                continue

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
                p_predict = subprocess.Popen("python3 predict.py '{}'".format(dcmdir_name), shell=True, cwd="/diana_direct/{}/package/src/".format(ml))
                p_predict.wait()

                with open("/opt/diana/{}_temp_predict".format(ml)) as f:
                    pred_bone_age = f.read()

                with open("/diana_direct/{}/{}_scores.txt".format(ml, ml), "a+") as f:
                    f.write("{}, {}".format(an, pred_bone_age))

                # Post to Slack
                sl_response = sl_client.chat_postMessage(
                    channel="DLEL863D0",
                    text="Accession Number: {},\n".format(an) +
                         "Bone Age Prediction (months): {}".format(pred_bone_age)
                )
                try:
                    assert(sl_response["ok"])
                except:
                    print("Error in Slack communication")

            os.remove("/diana_direct/{}/{}.studies.txt".format(ml, ml))
            time.sleep(180 // 3)  # ObservableProxiedDicom polling_interval / 3
    except (KeyboardInterrupt, json.decoder.JSONDecodeError, FileNotFoundError) as e:
        try:
            p_watch.send_signal(signal.SIGINT)
            p_collect.send_signal(signal.SIGINT)
            p_predict.send_signal(signal.SIGINT)
        except UnboundLocalError:
            pass
        if type(e) is json.decoder.JSONDecodeError:
            print("Excepted error: {}".format(e))
        elif type(e) is FileNotFoundError:
            print("Excepted error: {}".format(e))


def parse_results(json_lines, ml):
    accession_nums = []
    for line in json_lines:
        entry = json.loads(line.replace("\'", "\""))
        if ml == "bone_age" and entry['StudyDescription'] != 'X-Ray for Bone Age Study':
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
