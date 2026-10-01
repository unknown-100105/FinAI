from dataclasses import dataclass
from datetime import datetime
import re
from typing import Optional

from dateutil.relativedelta import relativedelta


@dataclass(frozen=True)
class MarketDateRange:
    start: datetime
    end: datetime
    reason: str


DEFAULT_HISTORY_YEARS = 1


def _normalize(text: str) -> str:
    return " ".join(
        str(text).strip().lower().split()
    )


def parse_market_date_range(
    text: str,
    now: Optional[datetime] = None,
) -> MarketDateRange:
    """
    Parse common natural-language market date ranges.

    Supported examples:
        last 7 days
        last 30 days
        last 3 weeks
        last 6 months
        last 1 year
        past year
        past month
        last 12 months

    If a historical request does not contain an explicit range,
    default to the previous one calendar year.
    """
    normalized = _normalize(text)
    end = now or datetime.now()

    # Explicit ISO date range:
    # 2026-01-01 to 2026-09-30
    explicit = re.search(
        r"(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})",
        normalized,
    )

    if explicit:
        start = datetime.strptime(
            explicit.group(1),
            "%Y-%m-%d",
        )

        explicit_end = datetime.strptime(
            explicit.group(2),
            "%Y-%m-%d",
        ).replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999,
        )

        if start > explicit_end:
            raise ValueError(
                "Market date range start must not be after end."
            )

        return MarketDateRange(
            start=start,
            end=explicit_end,
            reason="explicit_date_range",
        )

    # last/past N days|weeks|months|years
    match = re.search(
        r"\b(?:last|past)\s+(\d+)\s+"
        r"(day|days|week|weeks|month|months|year|years)\b",
        normalized,
    )

    if match:
        amount = int(match.group(1))
        unit = match.group(2)

        if amount <= 0:
            raise ValueError(
                "Market date-range amount must be positive."
            )

        if unit.startswith("day"):
            start = end - relativedelta(days=amount)
        elif unit.startswith("week"):
            start = end - relativedelta(weeks=amount)
        elif unit.startswith("month"):
            start = end - relativedelta(months=amount)
        else:
            start = end - relativedelta(years=amount)

        return MarketDateRange(
            start=start,
            end=end,
            reason=f"{amount}_{unit}",
        )

    # Common singular expressions.
    singular_ranges = {
        "past day": relativedelta(days=1),
        "last day": relativedelta(days=1),
        "past week": relativedelta(weeks=1),
        "last week": relativedelta(weeks=1),
        "past month": relativedelta(months=1),
        "last month": relativedelta(months=1),
        "past year": relativedelta(years=1),
        "last year": relativedelta(years=1),
        "past 12 months": relativedelta(months=12),
        "last 12 months": relativedelta(months=12),
    }

    for phrase, delta in singular_ranges.items():
        if phrase in normalized:
            return MarketDateRange(
                start=end - delta,
                end=end,
                reason=phrase.replace(" ", "_"),
            )

    return MarketDateRange(
        start=end - relativedelta(
            years=DEFAULT_HISTORY_YEARS
        ),
        end=end,
        reason="default_one_year",
    )
