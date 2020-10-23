from datetime import datetime
import glob
import shutil
import subprocess
import time

d1 = glob.glob("/reports/tmp/*.csv")
d2 = glob.glob("/reports/*.csv")

while True:
    print(datetime.now().strftime("%Y%m%d-%H%M%S"))
    for _ in d1:
        if _.split("/")[-1] not in [f.split("/")[-1] for f in d2]:
            print("Copied: {}".format(_))
            subprocess.Popen("cp {} /reports".format(_), shell=True)
    time.sleep(86400)
