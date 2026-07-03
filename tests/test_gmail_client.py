from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytest

from src.gmail_client import _decode_header_value, _extract_body, fetch_recent_emails


def test_decode_header_value_plain_ascii():
    assert _decode_header_value("Hello there") == "Hello there"


def test_decode_header_value_encoded_utf8():
    # "Café" subject encoded/decoded round trip
    encoded = "=?utf-8?b?Q2Fmw6k=?="
    assert _decode_header_value(encoded) == "Café"


def test_extract_body_plain_text_message():
    msg = MIMEText("Just a plain body.")
    assert _extract_body(msg) == "Just a plain body."


def test_extract_body_multipart_prefers_text_plain():
    msg = MIMEMultipart("alternative")
    msg.attach(MIMEText("<p>html body</p>", "html"))
    msg.attach(MIMEText("plain text body", "plain"))
    assert _extract_body(msg) == "plain text body"


def test_fetch_recent_emails_raises_without_credentials(monkeypatch):
    monkeypatch.delenv("GMAIL_ADDRESS", raising=False)
    monkeypatch.delenv("GMAIL_APP_PASSWORD", raising=False)
    with pytest.raises(RuntimeError, match="GMAIL_ADDRESS"):
        fetch_recent_emails()
