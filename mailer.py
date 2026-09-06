"""Send the digest by email."""

import logging
import smtplib
from email.message import EmailMessage

import config

log = logging.getLogger(__name__)


def send(subject, html):
    if not (config.SMTP_USER and config.SMTP_PASSWORD and config.EMAIL_TO):
        log.warning("SMTP credentials incomplete — skipping email")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.SMTP_USER
    message["To"] = config.EMAIL_TO
    message.set_content(
        "This digest is formatted as HTML. Open it in a client that renders HTML, "
        "or read the web version."
    )
    message.add_alternative(html, subtype="html")

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.send_message(message)
        log.info("Email sent to %s", config.EMAIL_TO)
        return True
    except Exception as exc:
        log.error("Email failed: %s", exc)
        return False
