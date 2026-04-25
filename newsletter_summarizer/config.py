import os
from dotenv import load_dotenv

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

DB_PATH = os.getenv("DB_PATH", "newsletter_summarizer/digests.db")

DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "8"))
DIGEST_MINUTE = int(os.getenv("DIGEST_MINUTE", "0"))

FETCH_LOOKBACK_HOURS = int(os.getenv("FETCH_LOOKBACK_HOURS", "24"))

DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "5001"))

NEWSLETTER_SENDERS = [
    s.strip()
    for s in os.getenv("NEWSLETTER_SENDERS", "").split(",")
    if s.strip()
]

MODEL_ID = "claude-sonnet-4-6"
