from datetime import datetime

import pytest

from orchestrator.market_date_parser import parse_market_date_range


FIXED_NOW = datetime(
    2026,
    10,
    2,
    12,
    0,
    0,
)


def test_last_7_days():
    result = parse_market_date_range(
        "show last 7 days",
        now=FIXED_NOW,
    )

    assert result.start == datetime(
        2026, 9, 25, 12, 0, 0
    )
    assert result.end == FIXED_NOW
    assert result.reason == "7_days"


def test_last_3_weeks():
    result = parse_market_date_range(
        "last 3 weeks",
        now=FIXED_NOW,
    )

    assert result.start == datetime(
        2026, 9, 11, 12, 0, 0
    )


def test_last_6_months():
    result = parse_market_date_range(
        "last 6 months",
        now=FIXED_NOW,
    )

    assert result.start == datetime(
        2026, 4, 2, 12, 0, 0
    )


def test_last_year():
    result = parse_market_date_range(
        "last year",
        now=FIXED_NOW,
    )

    assert result.start == datetime(
        2025, 10, 2, 12, 0, 0
    )


def test_last_12_months():
    result = parse_market_date_range(
        "last 12 months",
        now=FIXED_NOW,
    )

    assert result.start == datetime(
        2025, 10, 2, 12, 0, 0
    )


def test_past_month():
    result = parse_market_date_range(
        "past month",
        now=FIXED_NOW,
    )

    assert result.start == datetime(
        2026, 9, 2, 12, 0, 0
    )


def test_explicit_range():
    result = parse_market_date_range(
        "2026-01-01 to 2026-09-30",
        now=FIXED_NOW,
    )

    assert result.start == datetime(
        2026, 1, 1
    )

    assert result.end.year == 2026
    assert result.end.month == 9
    assert result.end.day == 30
    assert result.reason == "explicit_date_range"


def test_default_one_year():
    result = parse_market_date_range(
        "show historical data",
        now=FIXED_NOW,
    )

    assert result.start == datetime(
        2025, 10, 2, 12, 0, 0
    )
    assert result.reason == "default_one_year"


def test_zero_range_rejected():
    with pytest.raises(ValueError):
        parse_market_date_range(
            "last 0 days",
            now=FIXED_NOW,
        )
