"""Read-only Longbridge OpenAPI adapter for FinAI data ingestion."""

from __future__ import annotations

from datetime import date, datetime
import os
from typing import Any, Dict, List, Optional

from .normalize import json_safe


class LongbridgeIntegrationError(RuntimeError):
    """Raised when the Longbridge SDK is missing or cannot provide data."""


class LongbridgeClient:
    """Lazy wrapper over Longbridge Quote, Fundamental and Content SDK contexts.

    Required environment variables for API-key auth:
      LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET, LONGBRIDGE_ACCESS_TOKEN

    The wrapper intentionally exposes read-only methods; no order/trade API is used.
    """

    def __init__(
        self,
        quote_context: Any = None,
        fundamental_context: Any = None,
        content_context: Any = None,
        config: Any = None,
    ) -> None:
        self.quote_context = quote_context
        self.fundamental_context = fundamental_context
        self.content_context = content_context
        self.config = config
        self._sdk: Dict[str, Any] = {}

    @property
    def is_configured(self) -> bool:
        return bool(
            (self.config is not None)
            or (
                os.getenv("LONGBRIDGE_APP_KEY")
                and os.getenv("LONGBRIDGE_APP_SECRET")
                and os.getenv("LONGBRIDGE_ACCESS_TOKEN")
            )
        )

    def _load_sdk(self) -> Dict[str, Any]:
        if self._sdk:
            return self._sdk
        try:
            from longbridge.openapi import (
                AdjustType,
                Config,
                ContentContext,
                FinancialReportKind,
                FinancialReportPeriod,
                FundamentalContext,
                Period,
                QuoteContext,
            )
        except ImportError as exc:
            raise LongbridgeIntegrationError(
                "The Longbridge SDK is not installed. Run: pip install longbridge"
            ) from exc

        try:
            config = self.config or Config.from_env()
        except Exception as exc:
            raise LongbridgeIntegrationError(
                "Could not initialize Longbridge. Configure "
                "LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET and "
                "LONGBRIDGE_ACCESS_TOKEN, or use the SDK OAuth flow."
            ) from exc

        self.config = config
        if self.quote_context is None:
            self.quote_context = QuoteContext(config)
        if self.fundamental_context is None:
            self.fundamental_context = FundamentalContext(config)
        if self.content_context is None:
            self.content_context = ContentContext(config)

        self._sdk = {
            "AdjustType": AdjustType,
            "FinancialReportKind": FinancialReportKind,
            "FinancialReportPeriod": FinancialReportPeriod,
            "Period": Period,
        }
        return self._sdk

    @staticmethod
    def _require_context(context: Any, name: str) -> Any:
        if context is None:
            raise LongbridgeIntegrationError(
                f"Longbridge {name} context was not initialized."
            )
        return context

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        self._load_sdk()
        context = self._require_context(self.quote_context, "Quote")
        try:
            quotes = context.quote([str(symbol).strip().upper()])
        except Exception as exc:
            raise LongbridgeIntegrationError(
                f"Longbridge quote request failed for {symbol}: {exc}"
            ) from exc
        values = json_safe(quotes)
        if isinstance(values, list):
            if not values:
                raise LongbridgeIntegrationError(
                    f"Longbridge returned no quote for {symbol}."
                )
            values = values[0]
        if not isinstance(values, dict):
            raise LongbridgeIntegrationError(
                f"Longbridge returned an unexpected quote for {symbol}."
            )
        return values

    def get_history(
        self,
        symbol: str,
        start: date | datetime | str,
        end: date | datetime | str,
        interval: str = "1d",
    ) -> List[Dict[str, Any]]:
        sdk = self._load_sdk()
        context = self._require_context(self.quote_context, "Quote")
        start_date = _as_date(start)
        end_date = _as_date(end)
        if start_date > end_date:
            raise ValueError("History start must not be after end.")

        interval_key = str(interval).strip().lower()
        period_map = {
            "1d": "Day", "day": "Day", "daily": "Day",
            "1wk": "Week", "1w": "Week", "week": "Week",
            "1mo": "Month", "1mth": "Month", "month": "Month",
        }
        enum_name = period_map.get(interval_key)
        if enum_name is None:
            raise ValueError(
                "Longbridge history supports daily, weekly or monthly intervals."
            )
        period = getattr(sdk["Period"], enum_name, None)
        if period is None:
            raise LongbridgeIntegrationError(
                f"Installed Longbridge SDK has no Period.{enum_name}."
            )
        try:
            rows = context.history_candlesticks_by_date(
                str(symbol).strip().upper(),
                period,
                sdk["AdjustType"].NoAdjust,
                start_date,
                end_date,
            )
        except Exception as exc:
            raise LongbridgeIntegrationError(
                f"Longbridge history request failed for {symbol}: {exc}"
            ) from exc
        values = json_safe(rows)
        return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []

    def get_financials(
        self,
        symbol: str,
        period: str = "annual",
    ) -> Dict[str, Any]:
        sdk = self._load_sdk()
        context = self._require_context(self.fundamental_context, "Fundamental")
        period_key = str(period).strip().lower()
        period_enum_name = {
            "annual": "Annual",
            "quarterly": "QuarterlyFull",
            "q1": "Q1",
            "q2": "Q2",
            "q3": "Q3",
            "semiannual": "SemiAnnual",
        }.get(period_key)
        if period_enum_name is None:
            raise ValueError(
                "period must be annual, quarterly, q1, q2, q3 or semiannual."
            )
        report_period = getattr(
            sdk["FinancialReportPeriod"], period_enum_name, None
        )
        if report_period is None:
            raise LongbridgeIntegrationError(
                f"Installed Longbridge SDK has no FinancialReportPeriod.{period_enum_name}."
            )
        try:
            result = context.financial_report(
                str(symbol).strip().upper(),
                kind=sdk["FinancialReportKind"].All,
                period=report_period,
            )
        except Exception as exc:
            raise LongbridgeIntegrationError(
                f"Longbridge financial report failed for {symbol}: {exc}"
            ) from exc
        values = json_safe(result)
        if isinstance(values, dict):
            return values
        raise LongbridgeIntegrationError(
            f"Longbridge returned an unexpected financial report for {symbol}."
        )

    def get_news(self, symbol: str) -> List[Dict[str, Any]]:
        self._load_sdk()
        context = self._require_context(self.content_context, "Content")
        try:
            news = context.news(str(symbol).strip().upper())
        except Exception as exc:
            raise LongbridgeIntegrationError(
                f"Longbridge news request failed for {symbol}: {exc}"
            ) from exc
        values = json_safe(news)
        return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _as_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError as exc:
        raise ValueError(f"Invalid date: {value!r}") from exc
