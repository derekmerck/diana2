from datetime import datetime
import glob
import shutil
import time

d1 = glob.glob("/reports/tmp/*.csv")
d2 = glob.glob("/reports/*.csv")

while True:
    print(datetime.now().strftime("%Y%m%d-%H%M%S"))
    for _ in d1:
        if _ not in d2:
            shutil.copy(_, "/reports")
    time.sleep(86400)
