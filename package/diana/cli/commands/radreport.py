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
@click.argument('work_path', type=click.STRING)
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

        if not os.path.isfile('{}/CT_undone_accessions.txt'.format(work_path)):
            open('{}/CT_undone_accessions.txt'.format(work_path), 'a').close()
        if not os.path.isfile('{}/MR_undone_accessions.txt'.format(work_path)):
            open('{}/MR_undone_accessions.txt'.format(work_path), 'a').close()
        if not os.path.isfile('{}/done_accessions.txt'.format(work_path)):
            open('{}/done_accessions.txt'.format(work_path), 'a').close()

        CT_undone_accessions = load_accessions('{}/CT_undone_accessions.txt'.format(work_path))
        MR_undone_accessions = load_accessions('{}/MR_undone_accessions.txt'.format(work_path))
        done_accessions = load_accessions('{}/done_accessions.txt'.format(work_path))

        # Load last processed date
        start_date = "2024-11-01"
        last_date = "2024-02-26"
        with open('{}/last_date.txt'.format(work_path), 'r') as f:
            last_date = f.read().strip()
        print("Processing up to last date: {}".format(last_date))

        # SMTP Config
        sender = SmtpMessenger()
        sender.host = os.environ['MAIL_HOST']
        sender.port = os.environ['MAIL_PORT']
        sender.from_addr = os.environ['MAIL_FROM']
        sender.user = None
        sender.password = ""

        while True:
            # Rad-Report-CT
            print("Rad-Report-CT...")
            cmd = ["diana-cli", "mfind", "--start_date={}".format(start_date), "--end_date={}".format(last_date), "-j", "-q", CT_macro, "montage"]
            with open("{}/CT_temp_results.json".format(work_path), "w") as f:
                p_collect = subprocess.Popen(cmd, shell=False, stdout=f, stderr=subprocess.PIPE)
                p_collect.wait()
            # out, err = p_collect.communicate()

            json_results = parse_json("{}/CT_temp_results.json".format(work_path))
            CT_undone_accessions.extend(filter_new_accessions(json_results, CT_undone_accessions, done_accessions))

            for an in CT_undone_accessions:
                # Find all studies associated with patient and then sort by date to find most recent relevent follow-up study
                cmd = ["diana-cli", "mfind", "-j", "-a", str(an), "montage"]
                with open("{}/temp_MRN.json".format(work_path), "w") as f:
                    p_collect = subprocess.Popen(cmd, shell=False, stdout=f, stderr=subprocess.PIPE)
                    p_collect.wait()
                json_for_MRN_i = parse_json("{}/temp_MRN.json".format(work_path))
                MRN_i = json_for_MRN_i[0]["tags"]["PatientID"]
                original_report = json_for_MRN_i[0]["meta"]["ReportText"]
                start_date_i = parser.parse(json_for_MRN_i[0]["meta"]["StudyDateTime"])

                cmd = ["diana-cli", "mfind", "--start_date={}".format(start_date_i.strftime("%Y-%m-%d")), "--end_date={}".format(datetime.today().strftime("%Y-%m-%d")), "-j", "-q", str(MRN_i), "montage"]
                with open("{}/temp_patient_studies.json".format(work_path), "w") as f:
                    p_collect = subprocess.Popen(cmd, shell=False, stdout=f, stderr=subprocess.PIPE)
                    p_collect.wait()

                json_for_followups_i = parse_json("{}/temp_patient_studies.json".format(work_path))
                json_for_followups_i = [_ for _ in json_for_followups_i if _["tags"]["Modality"] is "CT"]   # only keep CT jsons
                
                # Try another day if there have been no possible interval follow-ups
                if len(json_for_followups_i) is 0:
                    continue
                elif len(json_for_followups_i) > 1:
                    print("{}: MULTIPLE FOLLOW-UP STUDIES".format(an))
                
                json_for_followups_i = sorted(json_for_followups_i, key=lambda x: parser.parse(x["meta"]["StudyDateTime"]))  # sort by date

                follow_up_an = 0
                follow_up_index = 0
                prelimer = ""
                attending = ""
                for i, j_i in enumerate(json_for_followups_i):
                    if int(j_i["tags"]["AccessionNumber"] is an):
                        continue
                    follow_up_an = j_i["tags"]["AccessionNumber"]
                    follow_up_report = j_i["meta"]["ReportText"]
                    prelimer = j_i["meta"]["PrelimingPhysiciansName"]
                    attending = j_i["meta"]["ReadingPhysiciansName"]
                    break

                # No follow-up found
                if follow_up_an is 0:
                    continue

                email_recipients = [get_email(prelimer), get_email(attending)]
                email_recipients.remove(None)
                if len(email_recipients) is 0:
                    sender._send("ALERT: Unfound emails for {} and {}".format(prelimer, attending), os.environ['SYS_ADMIN'])

                email_body = "Original Report:\n" + original_report + "\n\n--------------------------------------\n\n" + "Follow-up Report:\n" + follow_up_report

                # Notify relevant parties then delete accession
                sender._send(email_body, email_recipients)
                done_accessions.append(an)
                CT_undone_accessions.remove(an)          
                
                # TODO: may need to refilter done and undone at the end to account for reports that used both Rad-Report-CT/MR

            with open('{}/CT_undone_accessions.txt'.format(work_path), 'w') as f:
                for _ in CT_undone_accessions:
                    f.write(str(_) + '\n')


            # Rad-Report-MR
            print("Rad-Report-MR...")
            cmd = ["diana-cli", "mfind", "--start_date={}".format(start_date), "--end_date={}".format(last_date), "-j", "-q={}".format(MR_macro), "montage"]
            with open("{}/MR_temp_results.json".format(work_path), "w") as f:
                p_collect = subprocess.Popen(cmd, shell=False, stdout=f, stderr=subprocess.PIPE)
                p_collect.wait()

            json_results = parse_json("{}/MR_temp_results.json".format(work_path))
            MR_undone_accessions.extend(filter_new_accessions(json_results, MR_undone_accessions, done_accessions))

            for an in MR_undone_accessions:
                # Find all studies associated with patient and then sort by date to find most recent relevent follow-up study
                cmd = ["diana-cli", "mfind", "-j", "-a", str(an), "montage"]
                with open("{}/temp_MRN.json".format(work_path), "w") as f:
                    p_collect = subprocess.Popen(cmd, shell=False, stdout=f, stderr=subprocess.PIPE)
                    p_collect.wait()

                json_for_MRN_i = parse_json("{}/temp_MRN.json".format(work_path))
                MRN_i = json_for_MRN_i[0]["tags"]["PatientID"]
                original_report = json_for_MRN_i[0]["meta"]["ReportText"]
                start_date_i = parser.parse(json_for_MRN_i[0]["meta"]["StudyDateTime"])

                cmd = ["diana-cli", "mfind", "--start_date={}".format(start_date_i.strftime("%Y-%m-%d")), "--end_date={}".format(datetime.today().strftime("%Y-%m-%d")), "-j", "-q", str(MRN_i), "montage"]
                with open("{}/temp_patient_studies.json".format(work_path), "w") as f:
                    p_collect = subprocess.Popen(cmd, shell=False, stdout=f, stderr=subprocess.PIPE)
                    p_collect.wait()

                json_for_followups_i = parse_json("{}/temp_patient_studies.json".format(work_path))
                json_for_followups_i = [_ for _ in json_for_followups_i if _["tags"]["Modality"] is "MR"]   # only keep MR jsons
                
                # Try another day if there have been no possible interval follow-ups
                if len(json_for_followups_i) is 0:
                    continue
                elif len(json_for_followups_i) > 1:
                    print("{}: MULTIPLE FOLLOW-UP STUDIES".format(an))

                json_for_followups_i = sorted(json_for_followups_i, key=lambda x: parser.parse(x["meta"]["StudyDateTime"]))  # sort by date

                follow_up_an = 0
                follow_up_index = 0
                prelimer = ""
                attending = ""
                for i, j_i in enumerate(json_for_followups_i):
                    if int(j_i["tags"]["AccessionNumber"] is an):
                        continue
                    follow_up_an = j_i["tags"]["AccessionNumber"]
                    follow_up_report = j_i["meta"]["ReportText"]
                    prelimer = j_i["meta"]["PrelimingPhysiciansName"]
                    attending = j_i["meta"]["ReadingPhysiciansName"]
                    break

                # No follow-up found
                if follow_up_an is 0:
                    continue

                email_recipients = [get_email(prelimer), get_email(attending)]
                email_recipients.remove(None)
                if len(email_recipients) is 0:
                    sender._send("ALERT: Unfound emails for {} and {}".format(prelimer, attending), os.environ['SYS_ADMIN'])

                email_body = "Original Report:\n" + original_report + "\n\n-----------------------------\n\n" + "Follow-up Report:\n" + follow_up_report

                # Notify relevant parties then delete accession
                sender._send(email_body, email_recipients)
                done_accessions.append(an)
                MR_undone_accessions.remove(an)



            # Update last processed date
            with open('{}/last_date.txt'.format(work_path), "w") as f:
                f.write(datetime.today().strftime("%Y-%m-%d"))

            with open('{}/done_accessions.txt'.format(work_path), 'w') as f:
                for _ in done_accessions:
                    f.write(_ + '\n')

            print("Sleeping...\n")
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
            key, value = line.split(',')
            data_dict[key.strip()] = value.strip()
    return data_dict

def get_email(name, email_list):
    parts = name.split(",")
    if len(parts) != 2:
        return "Invalid name format"

    last_name = parts[0].strip()
    first_middle = parts[1].strip().split()
    first_name = first_middle[0]
    middle_name = ""
    if len(first_middle) > 1:
        middle_name = first_middle[1]

    first_last = first_name + " " + last_name
    
    # Default name search in format "first last"
    if email_list.get(first_last) is not None:
        return email_list[first_last]
    
    # Try with full name including middle initial
    return email_list.get(first_name + " " + middle_name + " " + last_name)

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
