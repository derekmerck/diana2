import click
from datetime import datetime
import json
import os
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
    subprocess.Popen("nohup diana-cli watch -r say_studies radarch None > /diana_direct/{}/{}_results.json".format(ml, ml), shell=True, stdout=subprocess.PIPE)
    if not os.path.isfile("/diana_direct/{}/{}_scores.txt".format(ml, ml)):
        open("/diana_direct/{}/{}_scores.txt".format(ml, ml), 'a').close()

    while True:
        print("Query {}".format(datetime.now()))
        while not os.path.isfile("/diana_direct/{}/{}_results.json".format(ml, ml)):
            time.sleep(5)

        with open("/diana_direct/{}/{}_results.json".format(ml, ml), 'r') as data_file:
            json_data = data_file.read()[31:]
        accession_nums = parse_results(json.loads(json_data))
        os.remove("/diana_direct/{}/{}_results.json".format(ml, ml))

        if os.path.isfile("/diana_direct/{}/{}.key.csv"):
            os.remove("/diana_direct/{}/{}.key.csv")
        subprocess.Popen("diana-cli collect {} /diana_direct/{} sticky_bridge radarch".format(ml, ml), shell=True)

        for i, an in enumerate(accession_nums):
            with open("/diana_direct/{}/{}_scores.txt".format(ml, ml)) as f:
                if an in f.read():
                    print("...duplicate a/n.")
                    continue

            print("Processing unique a/n: {}".format(an))
            os.rename("/diana_direct/{}/data/{}".format(ml, an), "/diana_direct/{}/data/{}.zip".format(ml, an))
            with zipfile.ZipFile("/diana_direct/{}/data/{}.zip".format(ml, an), 'r') as zip_ref:
                zip_ref.extractall("/diana_direct/{}/data/{}".format(ml, an))

            subdirs = get_immediate_subdirectories("/diana_direct/{}/data/{}".format(ml, an))
            for fn in subdirs:
                if an in fn:
                    dcmdir_name = fn
            subprocess.Popen("python3 predict.py /diana_direct/{}/data/{} > /diana_direct/{}/temp_predict.txt".format(ml, dcmdir_name, ml), shell=True, cwd="/diana_direct/{}/package/src/".format(ml))

            with open("/diana_direct/{}/temp_predict".format(ml)) as f:
                pred_bone_age = f.read().split(">>PREDICTED BONE AGE: ")[1]

            with open("/diana_direct/{}/{}_scores.txt", "a+") as f:
                f.write("{}, {}".format(an, pred_bone_age))

        os.remove("/diana_direct/{}/{}.studies.txt".format(ml, ml))
        time.sleep(180 // 3)  # ObservableProxiedDicom polling_interval / 3


def parse_results(results, ml):
    for i, entry in enumerate(results):
        if ml == "bone_age" and entry['StudyDescription'] != 'X-Ray for Bone Age Study':
            continue
        else:
            print("Found X-Ray for Bone Age Study...")
        accession_nums = []
        with open("/diana_direct/{}/{}.studies.txt".format(ml, ml), 'a+') as f:
            f.write(entry['AccessionNumber'])
            accession_nums.append(entry['AccessionNumber'])
        return accession_nums


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]
