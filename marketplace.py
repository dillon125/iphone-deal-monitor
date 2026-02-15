import logging
import re
import time
from typing import Dict, List
from urllib.parse import quote_plus

import requests

FB_SEARCH_URL = "https://www.facebook.com/marketplace/orlando/search"
FB_URL_PREFIX = "https://www.facebook.com"


def _extract_price(text: str) -> str:
    match = re.search(r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)", text)
    return f"${match.group(1)}" if match else "N/A"


def _normalize_url(url: str) -> str:
    if url.startswith("http"):
        return url
    if url.startswith("/"):
        return f"{FB_URL_PREFIX}{url}"
    return f"{FB_URL_PREFIX}/{url}"


def _extract_listing_hrefs(html: str) -> List[str]:
    # Marketplace listing links typically contain /marketplace/item/
    hrefs = re.findall(r'href=["\']([^"\']+/marketplace/item/[^"\']+)["\']', html)
    unique_hrefs = list(dict.fromkeys(hrefs))
    return [_normalize_url(url) for url in unique_hrefs]


def _extract_title_near_link(html: str, href: str) -> str:
    escaped = re.escape(href)
    pattern = re.compile(
        rf'href=["\']{escaped}["\'][^>]*>(.*?)</a>',
        flags=re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        return "Facebook Marketplace listing"

    raw_text = re.sub(r"<[^>]+>", " ", match.group(1))
    clean_text = re.sub(r"\s+", " ", raw_text).strip()
    return clean_text or "Facebook Marketplace listing"


def fetch_facebook_marketplace_keyword(keyword: str, timeout: int = 20) -> List[Dict[str, str]]:
    """Best-effort Marketplace collector using public search pages.

    Facebook may require auth/challenge pages depending on region/IP. In those cases
    this returns an empty list and logs a warning while the monitor continues.
    """
    url = f"{FB_SEARCH_URL}?query={quote_plus(keyword)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        logging.error("Facebook Marketplace fetch failed for keyword '%s': %s", keyword, exc)
        return []

    html = response.text
    lowered = html.lower()
    if "log in" in lowered and "facebook" in lowered and "marketplace" in lowered:
        logging.warning(
            "Facebook Marketplace appears to require login/challenge for keyword '%s'; skipping this cycle",
            keyword,
        )
        return []

    urls = _extract_listing_hrefs(html)
    if not urls:
        logging.warning("No Marketplace listings parsed for keyword '%s'", keyword)
        return []

    entries: List[Dict[str, str]] = []
    for listing_url in urls:
        title = _extract_title_near_link(html, listing_url)
        entries.append(
            {
                "title": title,
                "url": listing_url,
                "price": _extract_price(title),
                "location": "Orlando (Facebook Marketplace)",
                "summary": "",
                "source": "facebook_marketplace",
            }
        )

    logging.debug("Fetched %d Facebook Marketplace entries for keyword '%s'", len(entries), keyword)
    return entries


def fetch_facebook_marketplace_keywords(keywords: List[str], delay_seconds: float = 1.5) -> List[Dict[str, str]]:
    entries: List[Dict[str, str]] = []
    for i, keyword in enumerate(keywords):
        entries.extend(fetch_facebook_marketplace_keyword(keyword))
        if i < len(keywords) - 1:
            time.sleep(max(0.0, delay_seconds))
    return entries
