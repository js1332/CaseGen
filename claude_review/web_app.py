"""
Simple web front-end for the Golf Course Map Generator.

This is the backend for the web app that Claude Code should review.
"""

import io
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from map_fetch import search_courses, fetch_and_cache_course  # type: ignore
from svg_render import render_direct_to_png, STYLE_COLORS  # type: ignore


app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/api/themes")
def api_themes():
    return jsonify(sorted(STYLE_COLORS.keys()))


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    try:
        courses = search_courses(q)
    except Exception as e:
        return jsonify({"error": f"Search failed: {e}"}), 500

    return jsonify(courses)


@app.route("/api/render")
def api_render():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "Missing query parameter 'q'"}), 400

    theme = request.args.get("theme", "minimalist")
    if theme not in STYLE_COLORS:
        theme = "minimalist"

    try:
        size = int(request.args.get("size", "1200"))
    except ValueError:
        size = 1200

    try:
        candidates = search_courses(q)
        if not candidates:
            return jsonify({"error": f"No courses found for '{q}'"}), 404

        course = candidates[0]
        geojson = fetch_and_cache_course(course)
        if not geojson:
            return jsonify({"error": "Failed to load course geometry"}), 500

        png_bytes = render_direct_to_png(
            geojson=geojson,
            style_name=theme,
            size=size,
        )
    except Exception as e:
        return jsonify({"error": f"Render failed: {e}"}), 500

    buf = io.BytesIO(png_bytes)
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

