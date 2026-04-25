import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from . import config
from .email_fetcher import fetch_newsletters
from .summarizer import summarize_batch
from .storage import init_db, save_digest

logger = logging.getLogger(__name__)


def run_digest():
    """Fetch, summarize, and store the daily newsletter digest."""
    logger.info("Starting daily digest run")
    try:
        newsletters = fetch_newsletters()
        if not newsletters:
            logger.info("No newsletters found in the last %d hours", config.FETCH_LOOKBACK_HOURS)
            return

        enriched = summarize_batch(newsletters)
        run_date = datetime.now().strftime("%Y-%m-%d")
        save_digest(run_date, enriched)
        logger.info("Digest complete: %d newsletters processed", len(enriched))
    except Exception as exc:
        logger.exception("Digest run failed: %s", exc)


def start_scheduler():
    """Start the blocking scheduler for daily digest."""
    init_db()
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_digest,
        CronTrigger(hour=config.DIGEST_HOUR, minute=config.DIGEST_MINUTE),
        id="daily_digest",
        name="Daily Newsletter Digest",
        misfire_grace_time=3600,
    )
    logger.info(
        "Scheduler started — digest runs daily at %02d:%02d",
        config.DIGEST_HOUR,
        config.DIGEST_MINUTE,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
