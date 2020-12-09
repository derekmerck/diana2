import sys
sys.path.insert(0, "/opt/diana/package")
from diana.utils.gateways.requesters import requester
from crud.exceptions import GatewayConnectionError
from wuphf.endpoints import SmtpMessenger
import click
from datetime import datetime, timedelta
from distutils.dir_util import copy_tree
import os
import glob
from hashlib import md5
from math import floor, isnan
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

        sender = SmtpMessenger()
        sender.host = os.environ['MAIL_HOST']
        sender.port = os.environ['MAIL_PORT']
        sender.from_addr = os.environ['MAIL_FROM']
        sender.user = None
        sender.password = ""

        while True:
            req_emails = []
            data = {
                'token': os.environ['REDCAP_TOKEN'],
                'content': 'record',
                'format': 'csv',
                'returnFormat': 'json',
                'dateRangeBegin': last_time.strftime("%Y-%m-%d %H:%M:%S"),
                'dateRangeEnd': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            last_time = datetime.now()
            api_resp = reqstr._post('', data=data)
            with open("{}/{}.csv".format(req_path, datetime.now().strftime("%Y%m%d-%H%M%S")), "wb+") as f:
                f.write(api_resp)
            requests = glob.glob("{}/*.csv".format(req_path))
            if len(requests) == 0 or len(api_resp) < 10 or ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,0" in api_resp.decode('utf-8'):
                print("No new requests {}".format(datetime.now()))
                manual_file = False
                for _ in glob.glob("{}/*.csv".format(req_path)):
                    if os.stat(_).st_size > 1200:
                        print(os.stat(_).st_size)
                        manual_file = True
                        continue
                    os.remove(_)
                if not manual_file:
                    last_time = datetime.now()
                    time.sleep(wait_time)
                    continue

            time.sleep(1)
            requests = glob.glob("{}/*.csv".format(req_path))
            for req in requests:
                patient_list = pd.read_csv(req)
                t_start = datetime.now()
                for i, pid in enumerate(patient_list["locr_patient_id"]):
                    req_emails = []
                    if patient_list["locr_requestor_email"][i] not in req_emails:
                        req_emails.append(patient_list["locr_requestor_email"][i])

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
                    time.sleep(10)
                    p_collect = subprocess.Popen("diana-cli collect -a -c anon {} sticky_bridge radarch".format(tmp_path), shell=True)
                    p_collect.wait()

                    for k, an_pre in enumerate(accession_nums):
                        an = md5("{}".format(an_pre).encode('utf-8')).hexdigest()[:16]
                        if not os.path.isdir("{}/data/{}_process".format(tmp_path, an)):
                            try:
                                with zipfile.ZipFile("{}/data/{}.zip".format(tmp_path, an), 'r') as zip_ref:
                                    zip_ref.extractall("{}/data/{}_process".format(tmp_path, an))
                            except FileNotFoundError:
                                continue
                            os.remove("{}/data/{}.zip".format(tmp_path, an))

                        image_folders = [_[0] for _ in os.walk("{}/data/{}_process".format(tmp_path, an))]
                        for _ in image_folders:
                            fdcms = glob.glob(_ + "/*.dcm", recursive=True)
                            if len(fdcms) == 1:
                                if os.stat(fdcms[0]).st_size < 50000:
                                    os.remove(fdcms[0])
                            if "SR" in _:
                                shutil.rmtree(_)

                        dcmfolder = get_subdirectories(get_subdirectories("{}/data/{}_process".format(tmp_path, an))[0])[0]
                        print(dcmfolder)
                        comb_path = "/{}/({})({})({})({})".format(out_path,
                                                                  patient_list["sponsor_protocol_number"][i],
                                                                  pid,
                                                                  patient_list["date_of_scan{}".format(k+1)][i].replace("/", "."),
                                                                  dcmfolder.split("/")[-1])
                        print(comb_path)
                        copy_tree(dcmfolder, comb_path)
                        shutil.rmtree("{}/data/{}_process".format(tmp_path, an))
                    t_elapsed = datetime.now() - t_start
                    sender._send("NOTICE: an anonymization request was completed in {} min {} s".format(floor(t_elapsed.seconds / 60), t_elapsed.seconds % 60), patient_list["locr_requestor_email"][i])
                try:
                    shutil.move(req, "/locr/ArchivedRequests")
                except shutil.Error:
                    os.remove(req)
                    time.sleep(60)
    except (KeyboardInterrupt, FileNotFoundError, KeyError, AssertionError, GatewayConnectionError) as e:
        try:
            for _ in sub_processes:
                _.kill()
                # os.killpg(os.getpgid(_.pid), signal.SIGTERM)
        except UnboundLocalError:
            print("UnboundLocalError on exit clean-up")  # TODO: address
            pass

        if type(e) is FileNotFoundError:
            print("Excepted error: {}".format(e))
        elif type(e) is KeyError:
            print("Key Error: {}".format(e))
        elif type(e) is AssertionError:
            print("Slack Error: {}".format(e))
        elif type(e) is KeyboardInterrupt:
            print("Exiting...")
        elif type(e) is GatewayConnectionError:
            sender._send("Anonymizer cannot reach REDCap API", [os.environ['SYS_ADMIN1'], os.environ['SYS_ADMIN2']])
        else:
            print("Some error: {}".format(e))

        for _ in req_emails:
            print("Emailed: {}".format(_))
            sender._send("ERROR: Anonymization system is down. Please contact system administrator.", _)


def get_subdirectories(a_dir):
    return [f.path for f in os.scandir(a_dir) if f.is_dir()]
