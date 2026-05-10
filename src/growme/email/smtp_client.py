"""Local-SMTP email sender. Targets Mailpit at localhost:1025 by default.

Run Mailpit alongside the Streamlit app:
    mailpit
or
    docker run -p 1025:1025 -p 8025:8025 axllent/mailpit
View captured mail at http://localhost:8025.
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


class SMTPSendError(RuntimeError):
    pass


def send_email(to: str, subject: str, html: str) -> None:
    host = os.environ.get("GROWME_SMTP_HOST", "localhost")
    port = int(os.environ.get("GROWME_SMTP_PORT", "1025"))
    sender = os.environ.get("GROWME_SMTP_FROM", "growme@localhost")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("This message requires an HTML-capable mail client.")
    msg.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(host, port, timeout=5) as smtp:
            smtp.send_message(msg)
    except (OSError, smtplib.SMTPException) as e:
        raise SMTPSendError(
            f"Could not reach SMTP at {host}:{port} ({e}). "
            "Is Mailpit running? `mailpit` or `docker run -p 1025:1025 -p 8025:8025 axllent/mailpit`."
        ) from e
