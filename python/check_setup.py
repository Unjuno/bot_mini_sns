"""Validate environment configuration before starting a platform webhook."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / ".env", override=False)

REQUIRED = {
    "line": ("ACCESS_TOKEN", "CHANNEL_SECRET"),
    "telegram": ("TELEGRAM_BOT_TOKEN",),
    "discord": ("DISCORD_BOT_TOKEN",),
    "zulip": ("ZULIP_BASE_URL", "ZULIP_EMAIL", "ZULIP_API_KEY"),
    "matrix": ("MATRIX_BASE_URL", "MATRIX_ACCESS_TOKEN", "MATRIX_ROOM_ID"),
    "slack": ("SLACK_BOT_TOKEN",),
    "google_chat": ("GOOGLE_CHAT_ACCESS_TOKEN",),
    "viber": ("VIBER_AUTH_TOKEN",),
    "mastodon": ("MASTODON_BASE_URL", "MASTODON_ACCESS_TOKEN"),
    "misskey": ("MISSKEY_BASE_URL", "MISSKEY_TOKEN"),
    "bluesky": ("BLUESKY_ACCESS_JWT", "BLUESKY_REPO"),
    "whatsapp": ("WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"),
    "instagram": ("INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID"),
    "teams": ("TEAMS_BOT_TOKEN", "TEAMS_SERVICE_URL"),
    "kakaotalk": (),
    "twitch": ("TWITCH_ACCESS_TOKEN", "TWITCH_CLIENT_ID", "TWITCH_BROADCASTER_ID", "TWITCH_SENDER_ID"),
    "reddit": ("REDDIT_ACCESS_TOKEN",),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", default=os.getenv("PLATFORM", "line"))
    parser.add_argument("--offline", action="store_true", help="skip credential checks")
    args = parser.parse_args()
    platform = args.platform.strip().lower()
    if platform not in REQUIRED:
        print(f"Unknown platform: {platform}", file=sys.stderr)
        return 2
    if args.offline:
        print(f"OK: {platform} offline configuration")
        return 0
    missing = [name for name in REQUIRED[platform] if not os.getenv(name, "").strip()]
    if missing:
        print(f"Missing for {platform}: {', '.join(missing)}", file=sys.stderr)
        return 1
    print(f"OK: {platform} configuration is present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
