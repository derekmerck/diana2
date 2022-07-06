from os import environ
import platform
import subprocess
import sys
import time
sys.path.insert(0, environ["DIANA_PACKAGE_PATH"])
from diana2.package.wuphf.endpoints import SmtpMessenger

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
    host_to_monitor = sys.argv[1]

    sender = SmtpMessenger()
    sender.host = environ['MAIL_HOST']
    sender.port = environ['MAIL_PORT']
    sender.from_addr = environ['MAIL_FROM']
    sender.user = None
    sender.password = ""
    send_to = ["SYS_ADMIN1"]  # PRE-REQ: define recipient emails as environment variables

    while(True):
        online = ping(host_to_monitor)
        if not online:
            break
        time.sleep(60)

    sender._send("ALERT: Radiation dose monitoring server was unpingable",
                 [environ[_] for _ in send_to])

if __name__=="__main__":
    main()