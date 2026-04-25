"""
Entry point for the newsletter summarizer.

Usage:
  # Start the web dashboard (view past digests, trigger on-demand run)
  python -m newsletter_summarizer.main dashboard

  # Start the daily background scheduler (runs at DIGEST_HOUR:DIGEST_MINUTE)
  python -m newsletter_summarizer.main scheduler

  # Run a single digest immediately and exit
  python -m newsletter_summarizer.main run

  # Run both scheduler and dashboard together
  python -m newsletter_summarizer.main all
"""

import logging
import sys
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def _cmd_run():
    from .scheduler import run_digest
    from .storage import init_db
    init_db()
    run_digest()


def _cmd_dashboard():
    from .dashboard import start_dashboard
    start_dashboard()


def _cmd_scheduler():
    from .scheduler import start_scheduler
    start_scheduler()


def _cmd_all():
    from .dashboard import start_dashboard
    from .scheduler import start_scheduler

    t = threading.Thread(target=_cmd_scheduler, daemon=True)
    t.start()
    start_dashboard()


def main():
    commands = {
        "run": _cmd_run,
        "dashboard": _cmd_dashboard,
        "scheduler": _cmd_scheduler,
        "all": _cmd_all,
    }
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd not in commands:
        print(__doc__)
        sys.exit(1)
    commands[cmd]()


if __name__ == "__main__":
    main()
