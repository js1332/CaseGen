import imaplib
import email
import re
import logging
from datetime import datetime, timedelta, timezone
from email.header import decode_header
from email.utils import parsedate_to_datetime

from . import config

logger = logging.getLogger(__name__)

# Heuristic patterns that indicate a message is a newsletter
_NEWSLETTER_SUBJECT_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"newsletter",
        r"digest",
        r"weekly",
        r"daily",
        r"roundup",
        r"update[s]?\b",
        r"edition",
        r"issue\s*#?\d+",
        r"briefing",
        r"bulletin",
        r"recap",
    ]
]

_NEWSLETTER_HEADER_INDICATORS = {
    "list-unsubscribe",
    "list-id",
    "list-post",
    "x-mailer",
    "x-campaign",
    "x-mailchimp",
}


def _decode_str(raw) -> str:
    parts = decode_header(raw or "")
    decoded = []
    for chunk, enc in parts:
        if isinstance(chunk, bytes):
            decoded.append(chunk.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(chunk)
    return " ".join(decoded)


def _get_body(msg: email.message.Message) -> str:
    """Extract plain-text body, falling back to HTML stripped of tags."""
    plain, html = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if "attachment" in cd:
                continue
            if ct == "text/plain" and not plain:
                plain = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", errors="replace"
                )
            elif ct == "text/html" and not html:
                html = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", errors="replace"
                )
    else:
        ct = msg.get_content_type()
        payload = msg.get_payload(decode=True)
        if payload:
            text = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
            if ct == "text/plain":
                plain = text
            else:
                html = text

    if plain:
        return plain[:8000]

    # Strip HTML tags for a rough plain-text fallback
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:8000]


def _is_newsletter(msg: email.message.Message, subject: str) -> bool:
    """Return True if the message looks like a newsletter."""
    if config.NEWSLETTER_SENDERS:
        sender = _decode_str(msg.get("From", "")).lower()
        if any(s.lower() in sender for s in config.NEWSLETTER_SENDERS):
            return True

    # Check for mailing-list headers
    headers_lower = {k.lower() for k in msg.keys()}
    if headers_lower & _NEWSLETTER_HEADER_INDICATORS:
        return True

    # Check subject patterns
    if any(p.search(subject) for p in _NEWSLETTER_SUBJECT_PATTERNS):
        return True

    return False


def fetch_newsletters(lookback_hours: int = None) -> list[dict]:
    """
    Connect via IMAP, fetch emails from the last *lookback_hours* hours,
    filter for newsletters, and return a list of dicts.
    """
    hours = lookback_hours or config.FETCH_LOOKBACK_HOURS
    since_dt = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_str = since_dt.strftime("%d-%b-%Y")

    logger.info("Connecting to %s:%s", config.IMAP_HOST, config.IMAP_PORT)
    with imaplib.IMAP4_SSL(config.IMAP_HOST, config.IMAP_PORT) as imap:
        imap.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
        imap.select("INBOX", readonly=True)

        _, data = imap.search(None, f'(SINCE "{since_str}")')
        uid_list = data[0].split()
        logger.info("Found %d emails since %s", len(uid_list), since_str)

        newsletters = []
        for uid in uid_list:
            try:
                _, raw = imap.fetch(uid, "(RFC822)")
                msg = email.message_from_bytes(raw[0][1])

                subject = _decode_str(msg.get("Subject", "(no subject)"))
                sender = _decode_str(msg.get("From", ""))

                # Parse date and check it is within our window
                date_header = msg.get("Date")
                try:
                    msg_dt = parsedate_to_datetime(date_header)
                    if msg_dt.tzinfo is None:
                        msg_dt = msg_dt.replace(tzinfo=timezone.utc)
                    if msg_dt < since_dt:
                        continue
                except Exception:
                    pass

                if not _is_newsletter(msg, subject):
                    continue

                body = _get_body(msg)
                newsletters.append(
                    {
                        "uid": uid.decode(),
                        "subject": subject,
                        "sender": sender,
                        "date": date_header,
                        "body": body,
                    }
                )
                logger.info("Identified newsletter: %s", subject)
            except Exception as exc:
                logger.warning("Failed to process UID %s: %s", uid, exc)

    return newsletters
