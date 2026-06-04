"""CLI script: register the Telegram Bot webhook via the Bot API."""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def main() -> None:
    parser = argparse.ArgumentParser(description="Register Telegram webhook")
    parser.add_argument("--url", required=True, help="Public HTTPS base URL of the deployed app")
    parser.add_argument("--secret", default=None, help="Optional webhook secret token")
    args = parser.parse_args()

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in environment or .env", file=sys.stderr)
        sys.exit(1)

    webhook_url = args.url.rstrip("/") + "/telegram/webhook"
    payload: dict = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"],
    }
    secret = args.secret or os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if secret:
        payload["secret_token"] = secret

    resp = httpx.post(
        f"https://api.telegram.org/bot{token}/setWebhook",
        json=payload,
        timeout=15,
    )
    data = resp.json()
    if data.get("ok"):
        print(f"Webhook set: {webhook_url}")
    else:
        print(f"Failed: {data}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
