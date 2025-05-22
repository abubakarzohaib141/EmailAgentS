import streamlit as st
import imaplib
import email
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

st.set_page_config(page_title="📬 AI Email Assistant", layout="wide")
# Load .env values
load_dotenv()
EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
APP_PASSWORD = os.getenv("APP_PASSWORD")  # Added here
SENT_FILE = "sent_emails.json"

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["password_input"] = ""

    if not st.session_state["authenticated"]:
        pwd = st.text_input("Enter password:", type="password", key="password_input")
        if st.button("Submit"):
            if pwd == APP_PASSWORD:
                st.session_state["authenticated"] = True
              
            else:
                st.error("❌ Incorrect password")
        st.stop()


# Load sent emails from file
def load_sent_emails():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    return []

# Save new sent email
def save_sent_email(to, subject, body):
    sent = load_sent_emails()
    sent.append({"to": to, "subject": subject, "body": body})
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f)

# Send email
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)

    save_sent_email(to_email, subject, body)

# Fetch emails
def fetch_emails():
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")
    _, data = mail.search(None, 'ALL')
    email_ids = data[0].split()
    emails = []

    for eid in email_ids[-10:]:
        _, msg_data = mail.fetch(eid, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        subject = msg["subject"]
        from_ = msg["from"]
        date = msg["date"]

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()

        emails.append({"id": eid, "subject": subject, "from": from_, "date": date, "body": body})
    mail.logout()
    return emails

# Stub Gemini AI Reply
def generate_reply_gemini(prompt, api_key):
    return f"Gemini AI Reply to:\n\n{prompt}"

# CSS Styling
def add_custom_css():
    st.markdown("""
    <style>
        body {
            background-color: #f6f8fc;
        }
        .main {
            padding: 2rem;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0px 0px 10px #ccc;
        }
        .stButton > button {
            background-color: #1a73e8;
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
        }
        textarea {
            background-color: #f1f3f4;
        }
        input {
            background-color: #f1f3f4;
        }
    </style>
    """, unsafe_allow_html=True)

# Streamlit app
def main():
    check_password()  # <-- Added here for access control

    add_custom_css()

    st.sidebar.title("📧 Email Assistant")
    menu = st.sidebar.radio("Navigate", ["📥 Inbox", "✉️ Compose", "📤 Sent"])

    st.title("💼 AI Email Assistant")

    if menu == "📥 Inbox":
        st.subheader("📥 Inbox")
        emails = fetch_emails()
        selected = st.selectbox("Choose Email", emails, format_func=lambda x: f"{x['from']} — {x['subject']}")

        if selected:
            st.write(f"**From:** {selected['from']}")
            st.write(f"**Subject:** {selected['subject']}")
            st.write(f"**Date:** {selected['date']}")
            st.write("---")
            st.write(selected["body"])

            if st.button("🤖 Generate AI Reply"):
                prompt = f"Reply to this:\n\n{selected['body']}"
                ai_reply = generate_reply_gemini(prompt, GEMINI_API_KEY)
                st.text_area("✍️ Gemini Suggests:", ai_reply, height=150)

            manual_reply = st.text_area("📝 Your Reply")
            if st.button("📤 Send Reply"):
                send_email(selected["from"], "Re: " + selected["subject"], manual_reply)
                st.success("Reply sent!")

    elif menu == "✉️ Compose":
        st.subheader("✉️ Compose New Email")
        to = st.text_input("To:")
        subject = st.text_input("Subject:")
        body = st.text_area("Body:")

        if st.button("📤 Send Email"):
            send_email(to, subject, body)
            st.success("Email sent successfully!")

    elif menu == "📤 Sent":
        st.subheader("📤 Sent Emails")
        sent_emails = load_sent_emails()
        if not sent_emails:
            st.info("No emails sent yet.")
        for email_data in reversed(sent_emails):
            st.markdown(f"**To:** {email_data['to']}  \n**Subject:** {email_data['subject']}")
            st.markdown(email_data['body'])
            st.markdown("---")

if __name__ == "__main__":
    main()
