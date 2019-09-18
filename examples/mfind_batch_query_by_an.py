import json
import subprocess
import time
from diana.dixel import Dixel

fn = "/diana_direct/temp/unhidden.txt"
output = "/diana_direct/temp/unhidden.csv"
errors = []


def parse_results(results, fn):
    for i, entry in enumerate(results):
        record_i = Dixel.from_montage_json(entry)
        record_i.report.anonymize()
        record_i.to_csv("{}".format(fn))


with open(fn, 'r') as f:
    for an in f.readlines():
        if an == "":
            continue
        print("Querying a/n: {}".format(an))
        num_retries = 0
        try:
            subprocess.Popen("diana-cli mfind -j -a {} montage > /diana_direct/temp/temp_results.json".format(an), shell=True, stdout=subprocess.PIPE)
            num_retries = 0
        except:
            print("Error on a/n: {}".format(an))
            errors.append(an)

        with open("/diana_direct/temp/temp_results.json", 'r') as data_file:
            json_data = data_file.read()[12:]
        results = json.loads(json_data)
        parse_results(results, fn)

        time.sleep(3)

with open("/tmp/error_dates.txt", 'w') as f:
    for e in errors:
        f.write(e)
