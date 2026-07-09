"""
MCP Client — Gmail

Handles OAuth2 authentication and email operations via the Gmail API.
In tests, this module is mocked entirely.
"""

from __future__ import annotations

import base64
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _get_credentials() -> Credentials:
    """Build OAuth2 credentials from environment variables."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    # Refresh if needed
    if creds.expired or not creds.valid:
        creds.refresh(Request())
    return creds


def _build_message(to: str, subject: str, body: str, html: bool = False) -> dict:
    """Construct a Gmail API message payload."""
    if html:
        msg = MIMEMultipart("alternative")
        msg["to"] = to
        msg["subject"] = subject
        msg.attach(MIMEText(body, "html"))
    else:
        msg = MIMEText(body)
        msg["to"] = to
        msg["subject"] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


async def send_gmail(
    to: str,
    subject: str,
    body: str,
    html: bool = False,
) -> dict:
    """
    Send an email via Gmail API.

    Args:
        to: Recipient email address
        subject: Email subject line
        body: Email body (plain text or HTML)
        html: If True, send as HTML email

    Returns:
        Gmail API response dict
    """
    try:
        creds = _get_credentials()
        service = build("gmail", "v1", credentials=creds)
        message = _build_message(to=to, subject=subject, body=body, html=html)
        result = service.users().messages().send(userId="me", body=message).execute()
        logger.info(f"Email sent to {to} (id: {result.get('id')})")
        return result
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        raise
