import sys
sys.path.insert(0, "/opt/diana/package")
from diana.utils.gateways.requesters import requester
from crud.exceptions import GatewayConnectionError
from wuphf.endpoints import SmtpMessenger
import click
from datetime import datetime, timedelta
from dateutil import parser
import os
import json
from pathlib import Path
import subprocess
import time

import logging
logging.basicConfig(filename='/opt/diana/debug.log', level=logging.DEBUG)


@click.command(short_help="Image Follow-up Macro Pipeline")
@click.argument('req_path', type=click.STRING)
@click.argument('out_path', type=click.STRING)
@click.argument('tmp_path', type=click.STRING)
@click.pass_context
def radreport(ctx,
              work_path):
    """Examples:
    $ diana-cli radreport /working_dir
    """
    click.echo(click.style('Image Report Follow-Up Pipeline Initialized', underline=True, bold=True))
    try:
        with open('/opt/diana/debug.log', 'w'):
            pass
        sub_processes = []
        
        # Variables
        CT_macro = "Rad-Report-CT"
        MR_macro = "Rad-Report-MR"
        query_interval = 86400  # seconds in a day

        # Load all radiologist emails and uncompleted/completeted accessions from local .txt
        emails = load_emails('{}/emails.txt'.format(work_path))
        CT_undone_accessions = load_accessions('{}/CT_undone_accesions.txt'.format(work_path))
        MR_undone_accessions = load_accessions('{}/MR_undone_accesions.txt'.format(work_path))
        done_accessions = load_accessions('{}/done_accesions.txt'.format(work_path))

        # Load last processed date
        start_date = "2024-11-01"
        last_date = "2024-11-02"
        with open('{}/last_date.txt'.format(work_path), 'rb') as f:
            last_date = f.read()

        # SMTP Config
        sender = SmtpMessenger()
        sender.host = os.environ['MAIL_HOST']
        sender.port = os.environ['MAIL_PORT']
        sender.from_addr = os.environ['MAIL_FROM']
        sender.user = None
        sender.password = ""

        while True:
            # Rad-Report-CT
            p_collect = subprocess.Popen("diana-cli mfind -j --start_date={} --end_date={} -q {} montage > {}/CT_temp_results.json".format(start_date, last_date, CT_macro, work_path), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p_collect.wait()
            # out, err = p_collect.communicate()
            # time.sleep(5)

            json_results = parse_json("{}/CT_temp_results.json".format(CT_undone_accessions))
            CT_undone_accessions.extend(filter_new_accessions(json_results, CT_undone_accessions, done_accessions))

            for an in CT_undone_accessions:
                # Find all studies associated with patient and then sort by date to find most recent relevent follow-up study
                p_collect = subprocess.Popen('diana-cli mfind -j -a "{}" "montage" > {}/temp_MRN.json'.format(an, work_path), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p_collect.wait()
                json_for_MRN_i = parse_json("{}/temp_MRN.json".format(work_path))
                MRN_i = json_for_MRN_i[0]["tags"]["PatientID"]
                start_date_i = parser.parse(json_for_MRN_i[0]["meta"]["StudyDateTime"])

                p_collect = subprocess.Popen("diana-cli mfind -j --start_date={} --end_date={} -q {} montage > {}/temp_patient_studies.json".format(start_date_i, datetime.today().strftime("%Y-%m-%d"), MRN_i, work_path), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p_collect.wait()

                json_for_followups_i = parse_json("{}/temp_patient_studies.json".format(work_path))
                json_for_followsup_i = [_ for _ in json_for_followups_i if _["tags"]["modality"] is "CT"]   # only keep CT jsons
                
                # Try another day if there have been no possible interval follow-ups
                if len(json_for_followups_i) is 0:
                    continue
                
                json_for_followups_i = sorted(j_i, key=lambda x: parser.parse(x["meta"]["StudyDateTime"]))  # sort by date
                
                for j_i in json_for_followups_i:
                    



                # Notify relevant parties then delete accession
                sender._send("msg", "email recipient")
                done_accessions.append(an)
                CT_undone_accessions.remove(an)              
                

                time.sleep(3)


            # Rad-Report-MR
            # p_collect = subprocess.Popen("diana-cli mfind -j --start_date={} --end_date={} -q {} montage > {}/MR_temp_results.json".format(start_date, last_date, MR_macro, work_path), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # p_collect.wait()







            # Update last processed date and done/undone acccesions
            with open('{}/last_date.txt'.format(work_path), "w") as f:
                f.write(datetime.today().strftime("%Y-%m-%d"))



            
            time.sleep(query_interval)

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
        elif type(e) is KeyboardInterrupt:
            print("Exiting...")
        else:
            print("Some error: {}".format(e))

def load_emails(filepath):
    data_dict = {}
    with open(filepath, 'r') as file:
        for line in file:
            line = line.strip()
            key, value = line.split(';')
            data_dict[key.strip()] = value.strip()
    return data_dict

def load_accessions(filepath):
    accessions = []
    with open(filepath, 'r') as file:
        for line in file:
            accessions.append(int(line))
    return accessions

def parse_json(filepath):
    with open(filepath, 'r') as f:
        json_data = f.read()
    json_data = json_data[json_data.index('['):]
    return json.loads(json_data)

def filter_new_accessions(json_results, undone_accessions, done_accessions):
    new_accessions = []
    for dict_i in json_results:
        accession = int(dict_i["tags"]["AccessionNumber"])
        if accession not in undone_accessions and accession not in done_accessions:
            new_accessions.append(accession)
    return new_accessions
