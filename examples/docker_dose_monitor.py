from os import environ, execv
import sys
from datetime import datetime
import docker
import time
sys.path.insert(0, environ["DIANA_PACKAGE_PATH"]) # e.g. /home/username/**/diana2/package
from wuphf.endpoints import SmtpMessenger

client = docker.from_env()
sender = SmtpMessenger()
sender.host = environ['MAIL_HOST']
sender.port = environ['MAIL_PORT']
sender.from_addr = environ['MAIL_FROM']
sender.user = None
sender.password = ""
send_to = ["SYS_ADMIN1", "SYS_ADMIN2", "SYS_ADMIN3"]  # PRE-REQ: define recipient emails as environment variables

try:
    while True:
        if len(client.containers.list()) < 4:
            raise NotImplementedError
        print("Dose monitor likely online as of: {}".format(datetime.now()))
        time.sleep(60)
except Exception as e:
    sender._send("ALERT: Dose monitor Docker containers may be down. This alert monitor will auto-restart in 24 hours.",
                            [environ[_] for _ in send_to])

print("Monitor will restart in 24 hours...")
time.sleep(86400)
execv(sys.argv[0], sys.argv)