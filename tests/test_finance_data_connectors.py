from unittest.mock import Mock

import pytest

from finance_engine.data_sources.financial_datasets import (
    FinancialDatasetsClient,
    FinancialDatasetsError,
)
from finance_engine.data_sources.normalize import (
    normalize_longbridge_financial_reports,
)
from market_data.providers.longbridge_provider import (
    LongbridgeMarketDataProvider,
)
from market_data.models import MarketBar, MarketQuote
from scripts.build_finance_api_sft import build_sft_examples


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def test_financial_datasets_requires_api_key():
    client = FinancialDatasetsClient(api_key="", session=Mock())
    with pytest.raises(FinancialDatasetsError, match="FINANCIAL_DATASETS_API_KEY"):
        client.get_financials("AAPL")


def test_financial_datasets_sends_auth_and_query_params():
    session = Mock()
    session.get.return_value = FakeResponse(payload={"prices": []})
    client = FinancialDatasetsClient(
        api_key="test-key",
        base_url="https://api.financialdatasets.ai",
        session=session,
    )

    result = client.get_prices("AAPL", "2025-01-01", "2025-01-31")

    assert result == {"prices": []}
    args, kwargs = session.get.call_args
    assert args[0] == "https://api.financialdatasets.ai/prices"
    assert kwargs["headers"]["X-API-KEY"] == "test-key"
    assert kwargs["params"] == {
        "ticker": "AAPL",
        "interval": "day",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
    }


def test_financial_datasets_surfaces_credit_or_http_error_without_silencing():
    session = Mock()
    session.get.return_value = FakeResponse(
        status_code=402,
        payload={"detail": "Your current balance is $0.00."},
    )
    client = FinancialDatasetsClient(api_key="test-key", session=session)
    with pytest.raises(FinancialDatasetsError, match="balance is"):
        client.get_company_facts("AAPL")


def test_longbridge_report_normalization_groups_metrics_by_period():
    payload = {
        "list": {
            "i_s": {
                "indicators": [
                    {
                        "title": "营业收入",
                        "accounts": [{
                            "field": "OperatingRevenue",
                            "currency": "USD",
                            "values": [{
                                "year": 2025,
                                "period": "FY 2025",
                                "fp_end": "2025-09-27",
                                "value": "416161000000",
                                "yoy": "6.4",
                            }],
                        }],
                    },
                    {
                        "title": "净利润",
                        "accounts": [{
                            "field": "NetProfit",
                            "currency": "USD",
                            "values": [{
                                "year": 2025,
                                "period": "FY 2025",
                                "fp_end": "2025-09-27",
                                "value": "112010000000",
                                "yoy": "19.5",
                            }],
                        }],
                    },
                ]
            }
        }
    }
    records = normalize_longbridge_financial_reports(
        payload, "AAPL.US", "2026-10-22T00:00:00+00:00"
    )
    assert len(records) == 1
    assert records[0]["statement_type"] == "income_statement"
    assert records[0]["period"] == "FY 2025"
    assert records[0]["metrics"]["revenue"] == 416161000000.0
    assert records[0]["metrics"]["net_income"] == 112010000000.0


def test_sft_builder_deduplicates_agreeing_sources_and_excludes_conflicts():
    base = {
        "record_type": "financial_statement",
        "ticker": "AAPL.US",
        "statement_type": "income_statement",
        "period": "FY2025",
        "report_period": "2025-09-27",
        "currency": "USD",
        "metrics": {"revenue": 416161000000},
    }
    agreeing = [
        {**base, "source": "financial_datasets", "filing_url": "https://example.test/filing"},
        {**base, "source": "longbridge_openapi"},
    ]
    examples, conflicts = build_sft_examples(agreeing)
    assert len(examples) == 1
    assert not conflicts
    assert examples[0]["prompt"].startswith("For AAPL.US")
    assert "416,161,000,000 USD" in examples[0]["completion"]
    assert len(examples[0]["provider_sources"]) == 2

    disagreement = [
        agreeing[0],
        {**base, "source": "longbridge_openapi", "metrics": {"revenue": 123.0}},
    ]
    examples, conflicts = build_sft_examples(disagreement)
    assert not examples
    assert len(conflicts) == 1


def test_longbridge_market_provider_maps_quote_and_history():
    class FakeClient:
        def get_quote(self, symbol):
            assert symbol == "AAPL.US"
            return {
                "last_done": "344.55",
                "prev_close": "343.99",
                "open": "345",
                "high": "347.28",
                "low": "344.5",
                "volume": "5421471",
                "timestamp": "2026-10-22T14:14:04Z",
            }

        def get_history(self, symbol, start, end, interval):
            return [{
                "timestamp": "2026-10-22T14:00:00Z",
                "open": "345",
                "high": "347",
                "low": "344",
                "close": "346",
                "volume": "1200",
            }]

    from datetime import datetime, timezone
    provider = LongbridgeMarketDataProvider(client=FakeClient())
    quote = provider.get_quote("AAPL", "EQUITY", "US")
    assert isinstance(quote, MarketQuote)
    assert quote.price == 344.55
    assert quote.close == 343.99
    assert quote.source == "longbridge"

    bars = provider.get_history(
        "AAPL", "EQUITY",
        datetime(2026, 10, 22, tzinfo=timezone.utc),
        datetime(2026, 10, 23, tzinfo=timezone.utc),
        exchange="US",
    )
    assert len(bars) == 1
    assert isinstance(bars[0], MarketBar)
    assert bars[0].close == 346.0
