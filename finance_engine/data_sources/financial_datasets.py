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
    ) -> Dict[str, Any]:
        """Fetch historical OHLCV prices for one ticker."""
        return self._get(
            "/prices",
            {
                "ticker": ticker,
                "interval": interval,
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def get_financials(
        self,
        ticker: str,
        period: str = "annual",
    ) -> Dict[str, Any]:
        """Fetch normalized income, balance-sheet and cash-flow statements."""
        return self._get(
            "/financials",
            {"ticker": ticker, "period": period},
        )

    def get_news(
        self,
        ticker: str,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Fetch news metadata available for a company."""
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100.")
        return self._get("/news", {"ticker": ticker, "limit": int(limit)})

    def get_company_facts(self, ticker: str) -> Dict[str, Any]:
        """Fetch high-level company facts."""
        return self._get("/company/facts", {"ticker": ticker})
