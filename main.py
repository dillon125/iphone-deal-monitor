import json
import logging
import time
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from craigslist import fetch_all_keywords
from db import SeenListingsDB
from filters import passes_filters
from marketplace import fetch_facebook_marketplace_keywords
from notifier import notifier_from_env

CONFIG_PATH = Path("config.json")
POLL_INTERVAL_SECONDS = 60


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def collect_entries(config: Dict) -> List[Dict[str, str]]:
    keywords = config.get("keywords", [])
    if not keywords:
        return []

    entries: List[Dict[str, str]] = []

    if config.get("enable_craigslist", True):
        entries.extend(fetch_all_keywords(keywords, delay_seconds=config.get("request_delay_seconds", 1)))

    if config.get("enable_facebook_marketplace", False):
        entries.extend(
            fetch_facebook_marketplace_keywords(
                keywords,
                delay_seconds=config.get("facebook_request_delay_seconds", 2),
            )
        )

    return entries


def run() -> None:
    load_dotenv()
    configure_logging()

    config = load_config()
    keywords = config.get("keywords", [])
    if not keywords:
        raise ValueError("No keywords configured in config.json")

    db = SeenListingsDB(config.get("database_path", "listings.db"))
    notifier = notifier_from_env()

    logging.info("Starting iPhone deal monitor with %d keywords", len(keywords))
    logging.info(
        "Sources enabled: craigslist=%s, facebook_marketplace=%s",
        config.get("enable_craigslist", True),
        config.get("enable_facebook_marketplace", False),
    )

    while True:
        try:
            entries = collect_entries(config)

            for item in entries:
                url = item.get("url", "")
                if not url:
                    continue

                if db.has_seen(url):
                    logging.info("Item skipped (duplicate): %s", url)
                    continue

                is_valid, reason = passes_filters(item, config)
                if not is_valid:
                    logging.info("Item filtered out (%s): %s", reason, item.get("title", "Untitled"))
                    db.mark_seen(url)
                    continue

                source = item.get("source", "unknown")
                logging.info("New item detected [%s]: %s", source, item.get("title", "Untitled"))
                sent = notifier.send_listing(
                    title=item.get("title", "Untitled"),
                    price=item.get("price", "N/A"),
                    location=item.get("location", "Unknown"),
                    url=url,
                )

                if sent:
                    logging.info("Telegram sent successfully: %s", url)
                else:
                    logging.error("Telegram send failed: %s", url)

                db.mark_seen(url)

        except Exception as exc:
            logging.exception("Unexpected error in monitor loop: %s", exc)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
