import logging
from datetime import datetime

from flask import Flask, jsonify, render_template, request

from . import config
from .email_fetcher import fetch_newsletters
from .storage import get_latest_digest_id, get_newsletters_for_digest, get_recent_digests, init_db, save_digest
from .summarizer import summarize_batch

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    digests = get_recent_digests()
    digest_id = request.args.get("digest_id", type=int)
    if digest_id is None and digests:
        digest_id = digests[0]["id"]
    newsletters = get_newsletters_for_digest(digest_id) if digest_id else []
    return render_template(
        "newsletter_dashboard.html",
        digests=digests,
        newsletters=newsletters,
        active_digest_id=digest_id,
    )


@app.route("/api/digests")
def api_digests():
    return jsonify(get_recent_digests())


@app.route("/api/digests/<int:digest_id>/newsletters")
def api_newsletters(digest_id: int):
    return jsonify(get_newsletters_for_digest(digest_id))


@app.route("/api/run-digest", methods=["POST"])
def api_run_digest():
    try:
        newsletters = fetch_newsletters()
        enriched = summarize_batch(newsletters)
        run_date = datetime.now().strftime("%Y-%m-%d")
        digest_id = save_digest(run_date, enriched)
        return jsonify({"digest_id": digest_id, "count": len(enriched)})
    except Exception as exc:
        logger.exception("On-demand digest failed")
        return jsonify({"error": str(exc)}), 500


def start_dashboard():
    init_db()
    logger.info("Starting dashboard on port %d", config.DASHBOARD_PORT)
    app.run(host="0.0.0.0", port=config.DASHBOARD_PORT, debug=False)
