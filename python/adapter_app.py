"""Run any configured platform adapter as a persistent Flask webhook service."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request
from dotenv import load_dotenv

from core.service import SQLitePostRepository, process_event
from platforms import create_adapter


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / ".env", override=False)
PLATFORM = os.getenv("PLATFORM", "").strip().lower()
DATABASE_PATH = Path(os.getenv("ADAPTER_DATABASE_PATH", ROOT / "adapter_posts.db"))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = ROOT / DATABASE_PATH

app = Flask(__name__)
repository = SQLitePostRepository(DATABASE_PATH)
adapter = None
startup_error = None
if PLATFORM:
    try:
        adapter = create_adapter(PLATFORM, offline=os.getenv("OFFLINE", "false").lower() == "true")
    except (ValueError, NotImplementedError) as error:
        startup_error = str(error)
else:
    startup_error = "PLATFORM is required"


@app.get("/")
def health():
    return jsonify({"status": "ok", "platform": PLATFORM or None, "configured": adapter is not None}), 200


@app.post("/webhook")
def webhook():
    if adapter is None:
        return jsonify({"error": startup_error}), 503
    try:
        event = adapter.parse_event(request.get_json(force=True), dict(request.headers))
        reply = process_event(event, repository, adapter.capabilities.max_reply_items or 5)
        adapter.send_reply(event, reply)
        return jsonify(reply.model_dump()), 200
    except Exception as error:
        app.logger.exception("Platform webhook failed")
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
