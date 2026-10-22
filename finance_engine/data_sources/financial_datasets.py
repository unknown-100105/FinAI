"""Small read-only client for the Financial Datasets REST API."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests


class FinancialDatasetsError(RuntimeError):
    """Raised when the Financial Datasets API cannot supply a valid response."""


class FinancialDatasetsClient:
    """Read-only Financial Datasets client; credentials are read from the environment."""

    DEFAULT_BASE_URL = "https://api.financialdatasets.ai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 20.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = (
            api_key or os.getenv("FINANCIAL_DATASETS_API_KEY", "")
        ).strip()
        self.base_url = (
            base_url or os.getenv("FINANCIAL_DATASETS_BASE_URL")
            or self.DEFAULT_BASE_URL
        ).rstrip("/") + "/"
        self.timeout = float(timeout)
        self.session = session or requests.Session()

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise FinancialDatasetsError(
                "FINANCIAL_DATASETS_API_KEY is not configured."
            )

        url = urljoin(self.base_url, path.lstrip("/"))
        try:
            response = self.session.get(
                url,
                headers={"X-API-KEY": self.api_key, "Accept": "application/json"},
                params={key: value for key, value in params.items() if value is not None},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise FinancialDatasetsError(
                f"Financial Datasets request failed for {path}: {exc}"
            ) from exc

        if not 200 <= int(response.status_code) < 300:
            detail = ""
            try:
                payload = response.json()
                if isinstance(payload, dict):
                    detail = str(
                        payload.get("detail")
                        or payload.get("message")
                        or payload.get("error")
                        or ""
                    )
            except (ValueError, TypeError):
                detail = str(getattr(response, "text", ""))[:300]
            if not detail:
                detail = str(getattr(response, "text", ""))[:300]
            raise FinancialDatasetsError(
                f"Financial Datasets {path} failed with HTTP "
                f"{response.status_code}: {detail or 'no error detail returned'}"
            )

        try:
            payload = response.json()
        except (ValueError, TypeError) as exc:
            raise FinancialDatasetsError(
                f"Financial Datasets {path} returned invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise FinancialDatasetsError(
                f"Financial Datasets {path} returned an unexpected response shape."
            )
        return payload

    def get_prices(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "day",
        interval_multiplier: int = 1,
        limit: int = 5000,
    ) -> Dict[str, Any]:
        """Fetch historical OHLCV prices for one ticker."""
        if interval not in {"day", "week", "month", "year"}:
            raise ValueError("interval must be day, week, month or year.")
        if interval_multiplier < 1:
            raise ValueError("interval_multiplier must be at least 1.")
        if limit < 1 or limit > 5000:
            raise ValueError("limit must be between 1 and 5000.")
        return self._get(
            "/prices",
            {
                "ticker": ticker,
                "interval": interval,
                "interval_multiplier": int(interval_multiplier),
                "start_date": start_date,
                "end_date": end_date,
                "limit": int(limit),
            },
        )

    def get_financials(
        self,
        ticker: str,
        period: str = "annual",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Fetch income, balance-sheet and cash-flow statements from documented endpoints."""
        if period not in {"annual", "quarterly", "ttm"}:
            raise ValueError("period must be annual, quarterly or ttm.")
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100.")
        statements = {}
        endpoints = (
            ("income_statements", "/financials/income-statements"),
            ("balance_sheets", "/financials/balance-sheets"),
            ("cash_flow_statements", "/financials/cash-flow-statements"),
        )
        # Keep the output combined for downstream normalization. Errors remain
        # explicit; callers can record a failed request in the ingestion manifest.
        for key, path in endpoints:
            payload = self._get(
                path,
                {"ticker": ticker, "period": period, "limit": int(limit)},
            )
            rows = payload.get(key)
            if not isinstance(rows, list):
                raise FinancialDatasetsError(
                    f"Financial Datasets {path} returned no '{key}' list."
                )
            statements[key] = rows
        return statements

    def get_news(
        self,
        ticker: str,
        limit: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch news metadata available for a company."""
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100.")
        return self._get(
            "/news",
            {
                "ticker": ticker,
                "limit": int(limit),
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def get_company_facts(self, ticker: str) -> Dict[str, Any]:
        """Fetch high-level company facts."""
        return self._get("/company/facts", {"ticker": ticker})
