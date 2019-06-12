import csv
import json

from diana.dixel import RadiologyReport

json_file = "/Users/derek/Downloads/stanford_radcat_1k.jsonl"
output_csv = "/Users/derek/Desktop/stanford_radcat_1k.csv"

with open(output_csv, 'w', newline='') as csvFile:
    writer = csv.writer(csvFile)
    headers = ['id', 'modality', 'body_part',
               'cpt', 'sex', 'age',
               'status', 'radcat', 'radcat3',
               'radiologist', 'organization', 'report_text',
               'audit_radcat', 'agrees']
    writer.writerow(headers)
    with open(json_file) as f:
        for line in f:
            entry = json.loads(line)

            report = RadiologyReport(text=entry['report'])
            
            csvData = [entry['id'], entry['modality'].upper(), '',
                      '', 'U', '?',
                      '', entry['radcat_pred'], 'Yes' if entry['radcat_pred'] is 3 else 'No',
                      '', '', report.anonymized(),
                      '', '']
            writer.writerow(csvData)
csvFile.close()