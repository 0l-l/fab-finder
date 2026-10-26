"""Web front end for Fab Finder.

Usage:
    python server.py
then open http://127.0.0.1:5000

The page is static/index.html; this file only connects it to the same
functions the command-line app uses.
"""

from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from advisor import build_advice
from db import get_collection
from notes import DOMAINS, add_note, list_notes

STATIC_DIR = Path(__file__).parent / "static"
MAX_INPUT_CHARS = 1000

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")


@app.get("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.get("/api/stats")
def stats():
    total = get_collection().count()
    notes = len(list_notes())
    return jsonify({"wikipedia": total - notes, "notes": notes, "domains": DOMAINS})


@app.post("/api/advise")
def advise_route():
    query = (request.get_json(silent=True) or {}).get("query", "").strip()
    if not query:
        return jsonify({"error": "Describe what you need first."}), 400
    if len(query) > MAX_INPUT_CHARS:
        return jsonify({"error": f"Keep it under {MAX_INPUT_CHARS} characters."}), 400
    return jsonify(build_advice(query))


@app.get("/api/notes")
def get_notes():
    # Newest first on the web page.
    return jsonify(list(reversed(list_notes())))


@app.post("/api/notes")
def post_note():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Write the note first."}), 400
    if len(text) > MAX_INPUT_CHARS:
        return jsonify({"error": f"Keep notes under {MAX_INPUT_CHARS} characters."}), 400
    try:
        add_note(text, data.get("domain", ""), data.get("author", ""))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    return jsonify({"saved": True})


@app.errorhandler(Exception)
def handle_error(error):
    # Normal HTTP errors (like 404 Not Found) keep their own status code.
    if isinstance(error, HTTPException):
        return jsonify({"error": error.description}), error.code
    # Anything unexpected (e.g. no network for the embedding call) becomes a
    # readable message on the page instead of an HTML error page.
    return jsonify({"error": f"Something went wrong on the server: {error}"}), 500


if __name__ == "__main__":
    if not (STATIC_DIR / "index.html").exists():
        raise SystemExit(f"Can't find the web page. Put index.html in {STATIC_DIR}")
    print("Fab Finder is running at http://127.0.0.1:5000  (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=5000, debug=False)
