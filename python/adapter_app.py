"""Run any configured platform adapter as a persistent Flask webhook service."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request
from dotenv import load_dotenv

from core.service import SQLitePostRepository, process_event
from platforms import create_adapter
from platforms.catalog import PRODUCTION_READY
from platforms.security import verify_hmac_sha256, verify_hmac_sha256_hex, verify_slack_signature


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
    production_ready = PRODUCTION_READY.get(PLATFORM, False) if PLATFORM else False
    healthy = adapter is not None
    return jsonify({
        "status": "ok" if healthy else "not_ready",
        "platform": PLATFORM or None,
        "configured": healthy,
        "mode": "offline" if os.getenv("OFFLINE", "false").lower() == "true" else "production",
        "production_ready": production_ready,
        "error": startup_error,
    }), 200 if healthy else 503


@app.post("/webhook")
def webhook():
    if adapter is None:
        return jsonify({"error": startup_error}), 503
    try:
        raw_body = request.get_data(cache=True)
        headers = dict(request.headers)
        if PLATFORM == "line" and not verify_hmac_sha256(raw_body, os.getenv("CHANNEL_SECRET", ""), headers.get("X-Line-Signature", "")):
            return jsonify({"error": "invalid LINE signature"}), 401
        if PLATFORM == "slack" and not verify_slack_signature(raw_body, os.getenv("SLACK_SIGNING_SECRET", ""), headers.get("X-Slack-Request-Timestamp", ""), headers.get("X-Slack-Signature", "")):
            return jsonify({"error": "invalid Slack signature"}), 401
        if PLATFORM == "whatsapp" and not verify_hmac_sha256_hex(raw_body, os.getenv("WHATSAPP_APP_SECRET", ""), headers.get("X-Hub-Signature-256", ""), "sha256="):
            return jsonify({"error": "invalid WhatsApp signature"}), 401
        event = adapter.parse_event(request.get_json(force=True), headers)
        reply = process_event(event, repository, adapter.capabilities.max_reply_items or 5)
        adapter.send_reply(event, reply)
        return jsonify(reply.model_dump()), 200
    except Exception as error:
        app.logger.exception("Platform webhook failed")
        return jsonify({"error": str(error)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
