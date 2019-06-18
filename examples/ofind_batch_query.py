import json
import pandas as pd
import subprocess

# montage_results = r"D:\Google Drive\Brown\Research\Raw_Data\thyroid_bx_path\usbx\search_FNA thyroid-thru2015.csv", \
#                   r"D:\Google Drive\Brown\Research\Raw_Data\thyroid_bx_path\usbx\montage_thyroid_16-19.csv"

year = 2019
df = pd.read_csv("./thyroid_bx_path/usbx/montage_thyroid_16-19.csv", engine='python')


ofind_results = []
for i, AN in enumerate(df['Accession Number']):
    s_out = subprocess.Popen("diana-cli ofind -a {} -d radarch sticky_bridge".format(AN), shell=True, stdout=subprocess.PIPE).stdout.read()
    print("ACCESSION NUMBER: {}".format(AN))
    print(s_out)
    results = json.loads(s_out.decode("utf-8")[13:-1].replace('\'', '\"').replace('\n', ''))
    ofind_results.append(len(results))

print(df.shape)
print(len(ofind_results))
df['num ofind results'] = ofind_results
df.to_csv("./ofind_results_{}.csv".format(year))
