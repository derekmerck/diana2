import shutil
import glob

d1 = glob.glob("/reports/tmp/*.csv")
d2 = glob.glob("/reports/*.csv")

for _ in d1:
    if _ not in d2:
        shutil.copy(d1, "/reports")
