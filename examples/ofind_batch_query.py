import json
#import pandas as pd
import subprocess

# montage_results = r"D:\Google Drive\Brown\Research\Raw_Data\thyroid_bx_path\usbx\search_FNA thyroid-thru2015.csv", \
#                   r"D:\Google Drive\Brown\Research\Raw_Data\thyroid_bx_path\usbx\montage_thyroid_16-19.csv"

#year = 2019
#df = pd.read_csv("./thyroid_bx_path/usbx/montage_thyroid_16-19.csv", engine='python')

studies = "/elvos/elvos.studies.txt"
with open(studies) as f:
    accession_nums = [line.rstrip('\n') for line in f]

ofind_results = []
for i, AN in enumerate(accession_nums):
    print(AN)
    q_str = "diana-cli ofind -a {} ".format(AN) + "-l series -q \"{'SeriesDescription':''}\" -d radarch sticky_bridge"
    try:
        s_out = subprocess.Popen(q_str, shell=True, stdout=subprocess.PIPE).stdout.read()
        results = json.loads(s_out.decode("utf-8")[13:-1].replace('\'', '\"').replace('\n', ''))
    except:
        continue
    ofind_results += results
    with open("/elvos/jsons/{}.json".format(AN), "w") as f:
        json.dump(results, f)

with open("/elvos/series_descriptions.json", "w+") as f:
    json.dump(ofind_results, f)
