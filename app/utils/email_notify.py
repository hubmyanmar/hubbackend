from email.message import EmailMessage
import os
import smtplib


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


def send_decision_email(to_email: str, subject: str, body: str):
    try:
        if not SMTP_USER or not SMTP_PASSWORD:
            print("Skipping decision email: SMTP_USER or SMTP_PASSWORD is not configured")
            return

        message = EmailMessage()
        message["From"] = SMTP_USER
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(message)
    except Exception as exc:
        print(f"Failed to send decision email: {exc}")
