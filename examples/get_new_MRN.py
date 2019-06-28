import json
import pandas as pd
import subprocess

df = pd.read_csv("./thyroid_usbx_3daymatch_unrestrictedmatch.cancer_status.csv")

df['New MRN'] = [i for i in range(df.shape[0])]

new_MRNs = []

try:
    for i, AN in enumerate(df['Accession Number']):
        s_out = subprocess.Popen("diana-cli ofind -a {} -d radarch sticky_bridge".format(AN), shell=True, stdout=subprocess.PIPE).stdout.read()
        print("ACCESSION NUMBER: {}".format(AN))
        print(s_out)
        results = json.loads(s_out.decode("utf-8")[13:-1].replace('\'', '\"').replace('\n', ''))
        new_MRNs.append(results[0]["PatientID"])
        df['New MRN'][i] = results[0]["PatientID"]
except:
    print("{} error :(".format(AN))

df.to_csv("./New_MRNs.csv")
