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
import re
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

        # SMTP Config
        sender = SmtpMessenger()
        sender.host = os.environ['MAIL_HOST']
        sender.port = os.environ['MAIL_PORT']
        sender.from_addr = os.environ['MAIL_FROM']
        sender.user = None
        sender.password = ""

        while True:
            # Optional seconday downtime check
            try:
                if os.path.isfile("/{}/offline.txt".format(out_path.split("/")[1])):
                    os.remove("/{}/offline.txt".format(out_path.split("/")[1]))
            except:
                print("ERROR: failed to remove offline.txt")
                pass

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

            # Security limit
            if len(requests) > 10:
                print("Too many requests")
                quit()

            time.sleep(1)
            requests = glob.glob("{}/*.csv".format(req_path))
            for req in requests:
                comb_path = ""
                patient_list = pd.read_csv(req)
                t_start = datetime.now()

                req_emails = [patient_list["locr_requestor_email"][0]]

                try:
                    if isnan(patient_list["locr_requestor_email"][0]):
                        req_emails = ["adaas@lifespan.org"]
                except:
                    pass

                for i, pid in enumerate(patient_list["locr_patient_id"]):
                    try:
                        if isnan(pid):
                            continue
                    except TypeError:
                        print("ADAAS: Type error of some sort")
                        pass

                    accession_nums = []
                    for j in range(1, 11):
                        an_j = patient_list['accession_num{}'.format(j)][i]
                        if not isnan(an_j):
                            accession_nums.append(int(an_j))

                    if os.path.isfile("{}/anon.studies.txt".format(tmp_path)):
                        os.remove("{}/anon.studies.txt".format(tmp_path))
                    with open("{}/anon.studies.txt".format(tmp_path), 'a+') as f:
                        for an in accession_nums:
                            f.write(str(an) + "\n")

                    if os.path.isfile("{}/anon.key.csv".format(tmp_path)):
                        os.remove("{}/anon.key.csv".format(tmp_path))

                    with open("/opt/diana/pid.txt", "w+") as f:
                        f.write("{},{}".format(pid, patient_list["locr_study_name"][i]))

                    p_collect = subprocess.Popen("diana-cli collect -a -c anon {} sticky_bridge radarch201".format(tmp_path), shell=True)
                    p_collect.wait()
                    time.sleep(10)
                    p_collect = subprocess.Popen("diana-cli collect -a -c anon {} sticky_bridge radarch201".format(tmp_path), shell=True)
                    p_collect.wait()
                    time.sleep(5)
                    p_collect = subprocess.Popen("diana-cli collect -a -c anon {} sticky_bridge radarch201".format(tmp_path), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    p_collect.wait()
                    out, err = p_collect.communicate()
                    time.sleep(5)
                    if err:
                        raise NotImplementedError

                    for k, an_pre in enumerate(accession_nums):
                        an = md5("{}".format(an_pre).encode('utf-8')).hexdigest()[:16]
                        print("Processing: {}".format(an))
                        if not os.path.isdir("{}/data/{}_process".format(tmp_path, an)):
                            try:
                                print("Unzipping...")
                                with zipfile.ZipFile("{}/data/{}.zip".format(tmp_path, an), 'r') as zip_ref:
                                    zip_ref.extractall("{}/data/{}_process".format(tmp_path, an))
                            except FileNotFoundError:
                                print("Zip file not found--possible error with network/PACS pull?")
                                continue
                            os.remove("{}/data/{}.zip".format(tmp_path, an))

                        image_folders = [_[0] for _ in os.walk("{}/data/{}_process".format(tmp_path, an))]
                        for _ in image_folders:
                            if _.endswith(".") and _.startswith("."):
                                os.rename(_, _[1:-1])
                            elif _.startswith("."):
                                os.rename(_, _[1:])
                            elif _.endswith("."):
                                os.rename(_, _[:-1])
                            fdcms = glob.glob(_ + "/*.dcm", recursive=True)
                            for _fdcm in fdcms:
                                if _fdcm.split("/")[-1].startswith("US") or _fdcm.split("/")[-1].startswith("PR"):
                                    os.remove(_fdcm)
                                    print("Removed US or PR file: {}".format(_fdcm))
                                elif "CT Dose Report" in _fdcm:
                                    os.remove(_fdcm)
                                    print("Removed CT Dose Report: {}".format(_fdcm))
                                elif "XA Radiation Dose Information" in _fdcm:
                                    os.remove(_fdcm)
                                    print("Removed XA Radiation Dose Info: {}".format(_fdcm))
                                elif "OT Study acquired outside hospital" in _fdcm:
                                    os.remove(_fdcm)
                                    print("Removed OT Study acquired outside hospital: {}".format(_fdcm))    
                            if len(fdcms) == 1:
                                if os.path.isfile(fdcms[0]) and os.stat(fdcms[0]).st_size < 50000:
                                    os.remove(fdcms[0])
                                    print("Removed small file, presumed PHI: {}".format(fdcms[0]))
                            if re.search("SR\d\d\d\d\d\d", _):
                                shutil.rmtree(_)
                                print(_)
                                print("Removed SR folder")

                        time.sleep(3)  # time for cleanup
                        dcmfolder = get_subdirectories(get_subdirectories("{}/data/{}_process".format(tmp_path, an))[0])[0]
                        print(dcmfolder)
                        comb_path = "/{}/({})({})({})({})".format(out_path,
                                                                  patient_list["sponsor_protocol_number"][0],
                                                                  str(pid).replace("/", "."),
                                                                  str(patient_list["date_of_scan{}".format(k+1)][i]).replace("/", "."),
                                                                  dcmfolder.split("/")[-1])
                        print("comb_path: {}".format(comb_path))
                        copy_tree(dcmfolder, comb_path)
                        time.sleep(2)  # time to complete copy
                        print("Copy complete")
                        shutil.rmtree("{}/data/{}_process".format(tmp_path, an))
                        print("Removed data")
                    t_elapsed = datetime.now() - t_start
                    sender._send(("NOTICE: an anonymization request was completed in {} min {} s.\n"
                                  "You can access your anonymized imaging in the completed folder @ {}\n"
                                  "Total size: {} MB\n"
                                  "Thank you for using the Automated DICOM Attribute Anonymization System (ADAAS).").format(floor(t_elapsed.seconds / 60),
                                                                                                                            t_elapsed.seconds % 60,
                                                                                                                            os.environ['COMPLETED_FOLDER'],  # + "\\{}".format(comb_path.split("/")[-1]).replace(" ", "%20"),
                                                                                                                            get_dir_size(comb_path)),
                                 [sender.from_addr, req_emails[0]])
                try:
                    shutil.move(req, "/locr/ArchivedRequests")
                except shutil.Error:  # TODO: reinvestigate
                    os.remove(req)
                    time.sleep(60)
    except (NotImplementedError, KeyboardInterrupt, FileNotFoundError, KeyError, AssertionError, GatewayConnectionError, OSError, Exception) as e:
        try:
            for _ in sub_processes:
                _.kill()
                # os.killpg(os.getpgid(_.pid), signal.SIGTERM)
        except UnboundLocalError:
            print("UnboundLocalError on exit clean-up")  # TODO: address
            pass

        if type(e) is FileNotFoundError:
            print("Excepted error: {}".format(e))
        elif type(e) is NotImplementedError:
            print("Likely failure to collect accession error: {}".format(e))
            for _ in req_emails + [sender.from_addr]:
                print("Emailed: {}".format(_))
                sender._send("ERROR: The accession number you requested is currently not available. This could be due to being a new scan or a network issue. Please contact the system administrator for further information.", _)
            try:
                shutil.move(req, "/locr/FailedRequests")
            except shutil.Error:
                # TODO: change to os.rename
                os.remove(req)
                time.sleep(60)
            os.execv(sys.argv[0], sys.argv)
        elif type(e) is KeyError:
            print("Key Error: {}".format(e))
        elif type(e) is AssertionError:
            print("Slack Error: {}".format(e))
        elif type(e) is KeyboardInterrupt:
            print("Exiting...")
        elif type(e) is GatewayConnectionError:
            sender._send("Anonymizer cannot reach REDCap API. Will try restarting in an hour.", [sender.from_addr, os.environ['SYS_ADMIN1'], os.environ['SYS_ADMIN2']])
            time.sleep(3600)
            os.execv(sys.argv[0], sys.argv)
        else:
            print("Some error: {}".format(e))

        try:
            shutil.move(req, "/locr/FailedRequests")
        except shutil.Error:
            # TODO: change to os.rename
            # TODO: FileNotFoundError
            os.remove(req)

        for _ in req_emails:
            print("Emailed: {}".format(_))
            sender._send("ERROR: Anonymization system is down. Your request will be automatically reprocessed when the system is online.", _)
        sender._send("ERROR: Anonymization system is down. Please contact system administrator.", [sender.from_addr, os.environ['SYS_ADMIN1']])


def get_subdirectories(a_dir):
    return [f.path for f in os.scandir(a_dir) if f.is_dir()]


def get_dir_size(start_path):
    return int(sum(f.stat().st_size for f in Path(start_path).glob('**/*') if f.is_file()) / 1024 / 1024)  # MB
