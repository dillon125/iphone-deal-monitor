import logging
import time
from typing import Any, Dict, List

import feedparser
import requests

BASE_URL = "https://orlando.craigslist.org/search/sss"


def _extract_price(title: str) -> str:
    """Extract a Craigslist-style price from the title when present."""
    import re

    match = re.search(r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)", title)
    return f"${match.group(1)}" if match else "N/A"


def _extract_location(entry: Any) -> str:
    tags = getattr(entry, "tags", []) or []
    for tag in tags:
        term = tag.get("term") if isinstance(tag, dict) else None
        if term:
            return term

    title = getattr(entry, "title", "")
    if "(" in title and title.endswith(")"):
        return title.rsplit("(", 1)[-1][:-1].strip() or "Unknown"

    return "Unknown"


def normalize_entry(entry: Any) -> Dict[str, str]:
    title = getattr(entry, "title", "Untitled").strip()
    url = getattr(entry, "link", "").strip()
    return {
        "title": title,
        "url": url,
        "price": _extract_price(title),
        "location": _extract_location(entry),
        "summary": getattr(entry, "summary", "") or "",
        "source": "craigslist",
    }


def fetch_keyword_feed(keyword: str, timeout: int = 15) -> List[Dict[str, str]]:
    """Fetch and parse a single Craigslist RSS feed for a keyword."""
    params = {"query": keyword, "format": "rss"}
    headers = {"User-Agent": "iphone-deal-monitor/1.0"}

    try:
        response = requests.get(BASE_URL, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        logging.error("RSS fetch failed for keyword '%s': %s", keyword, exc)
        return []

    parsed = feedparser.parse(response.content)
    entries = [normalize_entry(item) for item in parsed.entries if getattr(item, "link", None)]
    logging.debug("Fetched %d entries for keyword '%s'", len(entries), keyword)
    return entries


def fetch_all_keywords(keywords: List[str], delay_seconds: float = 1.0) -> List[Dict[str, str]]:
    """Fetch all keywords with a small delay to avoid hammering Craigslist."""
    all_entries: List[Dict[str, str]] = []

    for i, keyword in enumerate(keywords):
        all_entries.extend(fetch_keyword_feed(keyword))
        if i < len(keywords) - 1:
            time.sleep(max(0.0, delay_seconds))

    return all_entries
