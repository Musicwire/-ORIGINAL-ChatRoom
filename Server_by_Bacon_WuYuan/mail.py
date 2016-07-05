import smtplib
import time
from email.message import Message
from time import sleep
import email.utils
import base64

smtpserver = 'smtp.163.com'
username = '1487225@qq.com'
password = 'dpg20140678'

from_addr = '1198487225@qq.com'
to_addr = 'bacontin@outlook.com'
cc_addr = ''

time = email.utils.formatdate(time.time(),True)

message = Message()
message['Subject'] = 'Mail Subject'
message['From'] = from_addr
message['To'] = to_addr
message['Cc'] = cc_addr
message.set_payload('mail content '+time)
msg = message.as_string()

sm = smtplib.SMTP(smtpserver,port=587,timeout=20)
sm.set_debuglevel(1)
sm.ehlo()
sm.starttls()
sm.ehlo()
sm.login(username, password)

sm.sendmail(from_addr, to_addr, msg)
sleep(5)
sm.quit()