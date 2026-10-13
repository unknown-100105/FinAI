from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import yfinance as yf

from policy.network_mode import assert_external_network_allowed


def _timestamp(value: Any) -> Optional[str]:
    if value is None:
        return None

    try:
        return datetime.fromtimestamp(
            int(value),
            tz=timezone.utc,
        ).isoformat()
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def _normalize_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None

    content = item.get("content")
    payload = content if isinstance(content, dict) else item

    title = (
        payload.get("title")
        or payload.get("headline")
        or item.get("title")
        or item.get("headline")
    )

    if not title:
        return None

    provider = (
        payload.get("provider", {}).get("displayName")
        if isinstance(payload.get("provider"), dict)
        else None
    ) or payload.get("publisher") or item.get("publisher")

    link = (
        payload.get("canonicalUrl", {}).get("url")
        if isinstance(payload.get("canonicalUrl"), dict)
        else None
    ) or payload.get("link") or payload.get("url") or item.get("link") or item.get("url")

    published = (
        payload.get("pubDate")
        or payload.get("published")
        or payload.get("providerPublishTime")
        or item.get("providerPublishTime")
    )

    return {
        "title": str(title).strip(),
        "publisher": str(provider).strip() if provider else None,
        "link": str(link).strip() if link else None,
        "published_at": (
            published
            if isinstance(published, str) and published.strip()
            else _timestamp(published)
        ),
        "type": payload.get("contentType") or item.get("type") or "news",
    }


def fetch_news(
    query: str,
    count: int = 10,
) -> List[Dict[str, Any]]:
    normalized_query = str(query).strip()

    if not normalized_query:
        raise ValueError("News query must not be empty.")

    count = max(1, min(int(count), 25))
    assert_external_network_allowed("yfinance financial news")

    try:
        search = yf.Search(
            normalized_query,
            max_results=5,
            news_count=count,
            include_cb=False,
        )
        raw_items = search.news or []
    except Exception as exc:
        raise RuntimeError(
            f"Financial news retrieval failed for '{normalized_query}': {exc}"
        ) from exc

    normalized = []

    for item in raw_items:
        record = _normalize_item(item)
        if record is not None:
            normalized.append(record)

        if len(normalized) >= count:
            break

    return normalized
