# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

from app.controller import update_db
import json


def send_email(gmail_mail, pwd, description):
    import smtplib

    gmail_user = gmail_mail
    gmail_pwd = pwd
    FROM = gmail_mail
    TO = [gmail_mail]  # must be a list
    SUBJECT = description['title']
    TEXT = description['contents']

    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
            """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        # server = smtplib.SMTP(SERVER)
        server = smtplib.SMTP("smtp.gmail.com", 587)  # or port 465 doesn't seem to work!
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        # server.quit()
        server.close()
        print 'successfully sent the mail'
    except:
        print "failed to send mail"


if __name__ == "__main__":
    with open("gmail.txt", 'r') as f:
        email = f.readline()
        pwd = f.readline()
        result = json.loads(update_db())
        if result['status'] == 'failed':
            send_email(email, pwd, result['description'])