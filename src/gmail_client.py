import email
import imaplib
import os
from dataclasses import dataclass
from email.header import decode_header
from email.message import Message

IMAP_HOST = "imap.gmail.com"


@dataclass
class InboxEmail:
    uid: str
    subject: str
    sender: str
    body: str

    @property
    def email_text(self) -> str:
        return f"Subject: {self.subject}\nFrom: {self.sender}\n\n{self.body}"


def _decode_header_value(raw_value: str) -> str:
    parts = decode_header(raw_value)
    decoded = []
    for text, charset in parts:
        if isinstance(text, bytes):
            decoded.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(text)
    return "".join(decoded)


def _extract_body(msg: Message) -> str:
    if not msg.is_multipart():
        payload = msg.get_payload(decode=True)
        if not payload:
            return ""
        charset = msg.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace").strip()

    for part in msg.walk():
        disposition = str(part.get("Content-Disposition", ""))
        if part.get_content_type() == "text/plain" and "attachment" not in disposition:
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace").strip()
    return ""


def _parse_message(uid: bytes, raw: bytes) -> InboxEmail:
    msg = email.message_from_bytes(raw)
    return InboxEmail(
        uid=uid.decode(),
        subject=_decode_header_value(msg.get("Subject", "(no subject)")),
        sender=_decode_header_value(msg.get("From", "(unknown sender)")),
        body=_extract_body(msg),
    )


def fetch_recent_emails(limit: int = 10) -> list[InboxEmail]:
    """Read-only fetch of the N most recent emails in INBOX via IMAP."""
    address = os.environ.get("GMAIL_ADDRESS")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    if not address or not app_password:
        raise RuntimeError(
            "GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set (see .env.example "
            "and the README for how to generate a Gmail app password)."
        )

    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    try:
        imap.login(address, app_password)
        imap.select("INBOX", readonly=True)

        status, data = imap.search(None, "ALL")
        if status != "OK":
            raise RuntimeError(f"IMAP search failed with status {status}")

        uids = data[0].split()[-limit:]
        emails = []
        for uid in reversed(uids):
            status, msg_data = imap.fetch(uid, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            emails.append(_parse_message(uid, msg_data[0][1]))
        return emails
    finally:
        imap.logout()
