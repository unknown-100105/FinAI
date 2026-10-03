from market_data.news import _normalize_item


def test_normalize_flat_news_item():
    result = _normalize_item(
        {
            "title": "Markets rise",
            "publisher": "Example Finance",
            "link": "https://example.com/article",
            "providerPublishTime": 1760000000,
        }
    )

    assert result["title"] == "Markets rise"
    assert result["publisher"] == "Example Finance"
    assert result["link"] == "https://example.com/article"
    assert result["published_at"].startswith("2025-")


def test_normalize_nested_news_item():
    result = _normalize_item(
        {
            "content": {
                "title": "TCS earnings",
                "provider": {"displayName": "Example News"},
                "canonicalUrl": {"url": "https://example.com/tcs"},
                "pubDate": "2026-10-03T08:00:00Z",
            }
        }
    )

    assert result["title"] == "TCS earnings"
    assert result["publisher"] == "Example News"
    assert result["link"] == "https://example.com/tcs"
    assert result["published_at"] == "2026-10-03T08:00:00Z"


def test_normalize_ignores_items_without_titles():
    assert _normalize_item({"publisher": "Example"}) is None
