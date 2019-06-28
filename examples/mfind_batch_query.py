from datetime import date, timedelta
import subprocess
import time

start_date = date(2003, 1, 1)
end_date = date(2019, 6, 25)
delta = end_date - start_date

errors = []
i = 0
num_retries = 0
while i < delta.days + 1:
    date_i = start_date + timedelta(days=i)
    print("Querying Date: {}".format(date_i))
    try:
        subprocess.Popen("diana-cli mfind --start_date={} --end_date={} -j -q \" \" montage > /montage_reports/{}_results.json".format(date_i, date_i, date_i), shell=True, stdout=subprocess.PIPE)
        num_retries = 0
    except:
        if num_retries < 3:
            print("Error on date: {}. Retrying...".format(date_i))
            errors.append(date_i)
            time.sleep(10)
            i -= 1
            num_retries += 1
    i += 1
    time.sleep(30)

with open("/montage_reports/error_dates.txt", 'w') as f:
    for e in errors:
        f.write(e)
