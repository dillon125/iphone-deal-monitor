from typing import Dict, List, Tuple


def _price_to_number(price: str) -> int | None:
    if not price or price == "N/A":
        return None
    digits = "".join(ch for ch in price if ch.isdigit())
    return int(digits) if digits else None


def passes_filters(item: Dict[str, str], config: Dict) -> Tuple[bool, str]:
    title = item.get("title", "")
    summary = item.get("summary", "")
    blob = f"{title} {summary}".lower()

    min_price = config.get("min_price")
    max_price = config.get("max_price")
    item_price = _price_to_number(item.get("price", ""))

    if min_price is not None and item_price is not None and item_price < min_price:
        return False, f"price below min_price ({item_price} < {min_price})"

    if max_price is not None and item_price is not None and item_price > max_price:
        return False, f"price above max_price ({item_price} > {max_price})"

    required_keywords: List[str] = [kw.lower() for kw in config.get("required_keywords", [])]
    if required_keywords and not any(kw in blob for kw in required_keywords):
        return False, "missing required keyword"

    blocked_keywords: List[str] = [kw.lower() for kw in config.get("blocked_keywords", [])]
    if any(kw in blob for kw in blocked_keywords):
        return False, "contains blocked keyword"

    return True, "passed"
