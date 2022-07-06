from os import environ, execv
import platform
import subprocess
import sys
import time
from datetime import datetime
sys.path.insert(0, environ["DIANA_PACKAGE_PATH"])
from wuphf.endpoints import SmtpMessenger

# Courtesy of: https://stackoverflow.com/questions/2953462/pinging-servers-in-python
def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command) == 0

def main():
    if len(sys.argv) < 2:
        sys.exit("Missing hostname argument")
    hosts_to_monitor = sys.argv[1:]

    sender = SmtpMessenger()
    sender.host = environ['MAIL_HOST']
    sender.port = environ['MAIL_PORT']
    sender.from_addr = environ['MAIL_FROM']
    sender.user = None
    sender.password = ""
    send_to = ["SYS_ADMIN1", "SYS_ADMIN2", "SYS_ADMIN3"]  # PRE-REQ: define recipient emails as environment variables

    restart = False
    while(True):
        for host in hosts_to_monitor:
            online = ping(host)
            time.sleep(1)
            if not online:
                sender._send("ALERT: {} was unpingable. Ping monitor will automatically restart in 24 hours.".format(host),
                             [environ[_] for _ in send_to])
                restart = True
        if restart:
            print("Monitor will restart in 24 hours...")
            time.sleep(86400)
            execv(sys.argv[0], sys.argv)
        print("Hosts online as of: {}".format(datetime.now()))
        time.sleep(60)

if __name__=="__main__":
    main()