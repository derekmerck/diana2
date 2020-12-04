import sys
sys.path.insert(0, r"D:\Git\diana2\package")
from wuphf.endpoints import SmtpMessenger

sender = SmtpMessenger()

sender.host = "smtp.xxx.com"
sender.port = 000
sender.from_addr = "...@..."
sender.user = "...@..."
sender.password = "pass"
sender.tls = True

sender._send("test msg", "dest_addr@...")
