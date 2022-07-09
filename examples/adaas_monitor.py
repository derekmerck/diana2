from os import environ, execv
from os.path import isfile
import sys
import time
from datetime import datetime
# sys.path.insert(0, environ["DIANA_PACKAGE_PATH"])
from ..package.wuphf.endpoints import SmtpMessenger

# Creates a file meant to be deleted by another entity every ~15 min. Alerts if file is not deleted.
def main():
    if len(sys.argv) < 2:
        sys.exit("Missing path of offline.txt argument")
    host = sys.argv[1:]

    sender = SmtpMessenger()
    sender.host = environ['MAIL_HOST']
    sender.port = environ['MAIL_PORT']
    sender.from_addr = environ['MAIL_FROM']
    sender.user = None
    sender.password = ""
    send_to = ["SYS_ADMIN1", "SYS_ADMIN2"]  # PRE-REQ: define recipient emails as environment variables

    count = 0
    online = True
    restart = False
    while(True):
        if isfile('{}/offline.txt'.format(host)):
            count += 1
        else:
            count = 0
  
        if count >= 2:
            online = False

        if not online:
            sender._send("ALERT: ADAAS communications may be offline. Secondary downtime monitor will auto-restart in 24 hours.",
                            [environ[_] for _ in send_to])
            restart = True
        if restart:
            print("Monitor will restart in 24 hours...")
            time.sleep(86400)
            execv(sys.argv[0], sys.argv)

        with open('{}/offline.txt'.format(host), 'w+'):
            pass
        print("ADAAS likely online as of: {}".format(datetime.now()))
        time.sleep(900)

if __name__=="__main__":
    main()