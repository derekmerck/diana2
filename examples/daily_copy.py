from datetime import datetime
import glob
import subprocess
import time

while True:
    d1 = glob.glob("/reports/tmp/*.csv")
    d2 = glob.glob("/reports/*.csv")
    print(datetime.now().strftime("%Y%m%d-%H%M%S"))
    for _ in d1:
        if _.split("/")[-1] not in [f.split("/")[-1] for f in d2]:
            print("Copied: {}".format(_))
            subprocess.Popen("cp {} /reports".format(_), shell=True)

    a = datetime.now()
    b = a.replace(day=a.day+1, hour=10, minute=0, second=0, microsecond=0)
    seconds_till_next = (a-b).seconds
    time.sleep(seconds_till_next)
