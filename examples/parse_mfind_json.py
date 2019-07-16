from diana.dixel import Dixel
import json
import os

directory = "/montage_reports"


def parse_results(results, fn):
    for i, entry in enumerate(results):
        record_i = Dixel.from_montage_json(entry)
        record_i.report.anonymize()
        record_i.to_csv("{}/{}.csv".format(directory, fn[:-5]))


for i, fn in enumerate(os.listdir(directory)):
    if fn.endswith(".json"):
        print(fn)
        file_path = os.path.join(directory, fn)
        with open(file_path, 'r') as data_file:
            json_data = data_file.read()[12:]
        results = json.loads(json_data)
        parse_results(results, fn)
