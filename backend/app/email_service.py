import os
import smtplib
from email.message import EmailMessage


def send_email(
    recipient,
    subject,
    body,
):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(
        os.getenv("SMTP_PORT", "587")
    )
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_sender = os.getenv(
        "SMTP_SENDER",
        smtp_username,
    )

    if not smtp_host:
        raise RuntimeError(
            "SMTP_HOST is not configured."
        )

    if not smtp_username:
        raise RuntimeError(
            "SMTP_USERNAME is not configured."
        )

    if not smtp_password:
        raise RuntimeError(
            "SMTP_PASSWORD is not configured."
        )

    if not smtp_sender:
        raise RuntimeError(
            "SMTP_SENDER is not configured."
        )

    message = EmailMessage()

    message["From"] = smtp_sender
    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=20,
    ) as server:

        server.starttls()

        server.login(
            smtp_username,
            smtp_password,
        )

        server.send_message(message)

    return True