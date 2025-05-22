import imaplib, email, smtplib
from email.mime.text import MIMEText
import os

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")

def get_sent_emails(query=""):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    mail.select('"[Gmail]/Sent Mail"')
    result, data = mail.search(None, "ALL")

    email_list = []
    for num in data[0].split()[-10:][::-1]:  # last 10 emails
        result, msg_data = mail.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])
        subject = msg["subject"]
        to = msg["to"]
        body = msg.get_payload(decode=True).decode(errors="ignore")
        if query.lower() in subject.lower() or query.lower() in body.lower():
            email_list.append({"uid": num.decode(), "to": to, "subject": subject, "body": body})
    return email_list

def delete_email(uid):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    mail.select('"[Gmail]/Sent Mail"')
    mail.store(uid, '+FLAGS', '\\Deleted')
    mail.expunge()
    mail.logout()

def send_email(to, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to, msg.as_string())
