import sys
sys.path.insert(0, "/opt/diana/package")
from diana.utils.gateways.requesters import requester
import click
from datetime import datetime, timedelta
from distutils.dir_util import copy_tree
import os
import glob
from hashlib import md5
from math import isnan
import pandas as pd
from pathlib import Path
import shutil
import subprocess
import time
import zipfile

import logging
logging.basicConfig(filename='/opt/diana/debug.log', level=logging.DEBUG)


@click.command(short_help="Anonymization Pipeline")
@click.argument('req_path', type=click.STRING)
@click.argument('out_path', type=click.STRING)
@click.argument('tmp_path', type=click.STRING)
@click.pass_context
def anonymize(ctx,
              req_path,
              out_path,
              tmp_path):
    """Examples:
    $ diana-cli anonymize /requests_dir /output_dir /temp_dir
    """
    click.echo(click.style('Anonymization Pipeline Initialized', underline=True, bold=True))
    try:
        with open('/opt/diana/debug.log', 'w'):
            pass
        sub_processes = []
        Path("{}/done_ids.txt".format(tmp_path)).touch()
        wait_time = 60  # seconds
        last_time = datetime.now() - timedelta(seconds=wait_time)
        reqstr = requester.Requester()
        reqstr.base_url = "https://redcap.lifespan.org/redcap/api"
        while True:
            data = {
                'token': os.environ['REDCAP_TOKEN'],
                'content': 'record',
                'format': 'csv',
                'returnFormat': 'json',
                'dateRangeBegin': last_time,
                'dateRangeEnd': datetime.now()
            }
            api_resp = reqstr._post('', data=data)
            with open("{}/{}.csv".format(req_path, datetime.now().strftime("%Y%m%d-%H%M%S")), "wb+") as f:
                f.write(api_resp)
            requests = glob.glob("{}/*.csv".format(req_path))
            if len(requests) == 0 or len(api_resp) < 10 or ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,0" in api_resp.decode('utf-8'):
                print("No new requests {}".format(datetime.now()))
                for _ in glob.glob("{}/*.csv".format(req_path)):
                    os.remove(_)
                last_time = datetime.now()
                time.sleep(wait_time)
                continue

            for req in requests:
                patient_list = pd.read_csv(req)
                for i, pid in enumerate(patient_list["locr_patient_id"]):
                    with open("{}/done_ids.txt".format(tmp_path)) as done_ids:
                        if str(patient_list["record_id"][i]) in done_ids.read():
                            print("Duplicate request record id...")
                            continue

                    accession_nums = []
                    for j in range(1, 11):
                        an_j = patient_list['accession_num{}'.format(j)][i]
                        if not isnan(an_j):
                            accession_nums.append(an_j)

                    if os.path.isfile("{}/anon.studies.txt".format(tmp_path)):
                        os.remove("{}/anon.studies.txt".format(tmp_path))
                    with open("{}/anon.studies.txt".format(tmp_path), 'a+') as f:
                        for an in accession_nums:
                            f.write(str(an) + "\n")

                    if os.path.isfile("{}/anon.key.csv".format(tmp_path)):
                        os.remove("{}/anon.key.csv".format(tmp_path))

                    with open("/opt/diana/pid.txt", "w+") as f:
                        f.write("{},{}".format(pid, patient_list["locr_study_name"][i]))

                    p_collect = subprocess.Popen("diana-cli collect -a -c anon {} sticky_bridge radarch".format(tmp_path), shell=True)
                    p_collect.wait()
                    time.sleep(10)
                    p_collect = subprocess.Popen("diana-cli collect -a -c anon {} sticky_bridge radarch".format(tmp_path), shell=True)
                    p_collect.wait()

                    if not os.path.isdir("{}/{}".format(out_path, pid)):
                        os.mkdir("{}/{}".format(out_path, pid))
                    for an_pre in accession_nums:
                        an = md5("{}".format(an_pre).encode('utf-8')).hexdigest()[:16]
                        if not os.path.isdir("{}/data/{}_process".format(tmp_path, an)):
                            # os.rename("{}/data/{}".format(tmp_path, an), "{}/data/{}.zip".format(tmp_path, an))
                            with zipfile.ZipFile("{}/data/{}.zip".format(tmp_path, an), 'r') as zip_ref:
                                zip_ref.extractall("{}/data/{}_process".format(tmp_path, an))
                            os.remove("{}/data/{}.zip".format(tmp_path, an))

                            image_folders = [_[0] for _ in os.walk("{}/data/{}_process".format(tmp_path, an))]
                            for _ in image_folders:
                                if "SR" in _:
                                    shutil.rmtree(_)
                            copy_tree("{}/data/{}_process".format(tmp_path, an), "{}/{}/{}".format(out_path, pid, an))
                            shutil.rmtree("{}/data/{}_process".format(tmp_path, an))
                    with open("{}/done_ids.txt".format(tmp_path), "a+") as f:
                        f.write(str(patient_list["record_id"][i]) + "\n")
                shutil.move(req, "/locr/ArchivedRequests")
    except (KeyboardInterrupt, FileNotFoundError, KeyError, AssertionError) as e:
        if type(e) is FileNotFoundError:
            print("Excepted error: {}".format(e))
        elif type(e) is KeyError:
            print("Key Error: {}".format(e))
        elif type(e) is AssertionError:
            print("Slack Error: {}".format(e))
        elif type(e) is KeyboardInterrupt:
            print("Exiting...")
        else:
            print("Some error: {}".format(e))

        try:
            for _ in sub_processes:
                _.kill()
                # os.killpg(os.getpgid(_.pid), signal.SIGTERM)
        except UnboundLocalError:
            print("UnboundLocalError on exit clean-up")  # TODO: address
            pass
