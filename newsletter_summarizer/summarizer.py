import logging
import anthropic

from . import config

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


_SYSTEM_PROMPT = """\
You are an expert newsletter analyst. When given the content of an email newsletter,
produce a concise digest in the following JSON format (respond ONLY with valid JSON):

{
  "summary": "<2-4 sentence overview of the newsletter>",
  "key_takeaways": ["<takeaway 1>", "<takeaway 2>", "<takeaway 3>"],
  "topics": ["<topic1>", "<topic2>"],
  "sentiment": "positive|neutral|negative",
  "must_read": true|false
}

Rules:
- key_takeaways: 3-5 most actionable or important points
- topics: 1-3 short category labels (e.g. "AI", "Finance", "Health")
- must_read: true if the content is time-sensitive or highly important
- Be factual and concise; do not editorialize
"""


def summarize_newsletter(subject: str, sender: str, body: str) -> dict:
    """
    Call Claude to summarize a newsletter and return a structured dict.
    Falls back to a minimal dict on any error.
    """
    prompt = f"Subject: {subject}\nFrom: {sender}\n\n---\n\n{body}"

    try:
        client = _get_client()
        response = client.messages.create(
            model=config.MODEL_ID,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()
        result = json.loads(raw)
        logger.info("Summarized: %s", subject)
        return result
    except Exception as exc:
        logger.error("Summarization failed for '%s': %s", subject, exc)
        return {
            "summary": "Could not generate summary.",
            "key_takeaways": [],
            "topics": [],
            "sentiment": "neutral",
            "must_read": False,
        }


def summarize_batch(newsletters: list[dict]) -> list[dict]:
    """Summarize a list of newsletter dicts (as returned by email_fetcher)."""
    results = []
    for nl in newsletters:
        analysis = summarize_newsletter(nl["subject"], nl["sender"], nl["body"])
        results.append({**nl, "analysis": analysis})
    return results
