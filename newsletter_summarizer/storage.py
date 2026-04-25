import json
import sqlite3
import logging
from datetime import datetime

from . import config

logger = logging.getLogger(__name__)


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS digests (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date    TEXT NOT NULL,
                fetched_at  TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS newsletters (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                digest_id   INTEGER NOT NULL REFERENCES digests(id),
                uid         TEXT,
                subject     TEXT,
                sender      TEXT,
                date        TEXT,
                summary     TEXT,
                takeaways   TEXT,
                topics      TEXT,
                sentiment   TEXT,
                must_read   INTEGER DEFAULT 0
            )
        """)
        con.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_digest_uid
            ON newsletters(digest_id, uid)
        """)


def save_digest(run_date: str, newsletters: list[dict]) -> int:
    """Persist a full digest run; return the digest id."""
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO digests(run_date) VALUES (?)", (run_date,)
        )
        digest_id = cur.lastrowid

        for nl in newsletters:
            analysis = nl.get("analysis", {})
            takeaways = json.dumps(analysis.get("key_takeaways", []))
            topics = json.dumps(analysis.get("topics", []))
            con.execute(
                """
                INSERT OR IGNORE INTO newsletters
                    (digest_id, uid, subject, sender, date,
                     summary, takeaways, topics, sentiment, must_read)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    digest_id,
                    nl.get("uid"),
                    nl.get("subject"),
                    nl.get("sender"),
                    nl.get("date"),
                    analysis.get("summary"),
                    takeaways,
                    topics,
                    analysis.get("sentiment", "neutral"),
                    int(bool(analysis.get("must_read", False))),
                ),
            )
    logger.info("Saved digest %d with %d newsletters", digest_id, len(newsletters))
    return digest_id


def get_recent_digests(limit: int = 7) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM digests ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_newsletters_for_digest(digest_id: int) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM newsletters WHERE digest_id = ? ORDER BY must_read DESC, id",
            (digest_id,),
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["takeaways"] = json.loads(d["takeaways"] or "[]")
        d["topics"] = json.loads(d["topics"] or "[]")
        result.append(d)
    return result


def get_latest_digest_id() -> int | None:
    with _conn() as con:
        row = con.execute("SELECT id FROM digests ORDER BY id DESC LIMIT 1").fetchone()
    return row["id"] if row else None
