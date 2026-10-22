"""Ingest licensed provider data into a local, attributable JSONL corpus.

Nothing in this script places orders. Raw provider data stays local and should not
be committed to source control; review provider license and redistribution terms
before using it in training or serving it to end users.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

# Local secrets stay in .env (excluded from Git). Existing shell variables win.
load_dotenv(ROOT / ".env", override=False)

from finance_engine.data_sources.financial_datasets import (
    FinancialDatasetsClient,
    FinancialDatasetsError,
)
from finance_engine.data_sources.longbridge import (
    LongbridgeClient,
    LongbridgeIntegrationError,
)
from finance_engine.data_sources.normalize import (
    find_list,
    json_safe,
    normalize_longbridge_financial_reports,
    normalize_metric_name,
    to_number,
)


DEFAULT_TICKERS = "AAPL.US,NVDA.US,MSFT.US"
STATEMENTS = (
    ("income_statements", "income_statement"),
    ("balance_sheets", "balance_sheet"),
    ("cash_flow_statements", "cash_flow_statement"),
)
PRICE_KEYS = ("prices", "stock_prices", "historical_prices", "price_bars")
NEWS_KEYS = ("news", "company_news", "articles", "results")

_METADATA_FIELDS = {
    "ticker", "symbol", "period", "fiscal_period", "report_period",
    "filing_date", "filing_datetime", "filing_url", "accession_number",
    "currency", "updated_at", "created_at", "date", "datetime",
    "timestamp", "time", "interval", "exchange", "source", "url",
    "news_url", "title", "description", "summary", "content",
    "headline", "published_at", "published", "id", "cik", "name",
    "sector", "industry", "category", "sic_code", "sic_industry",
    "sic_sector", "website_url", "sec_filings_url", "location",
    "listing_date", "is_active", "number_of_employees",
    "weighted_average_shares", "events",
}


def fd_ticker(symbol: str) -> str:
    """Financial Datasets uses the base ticker rather than Longbridge suffixes."""
    return str(symbol).strip().upper().split(".", 1)[0]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _records_from_mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _metric_values(row: Dict[str, Any]) -> Dict[str, float]:
    metrics: Dict[str, float] = {}
    for key, value in row.items():
        if str(key).lower() in _METADATA_FIELDS:
            continue
        if str(key).endswith("_yoy") or str(key).endswith("_growth"):
            # Keep growth rates under a namespaced key to avoid confusing them
            # with absolute financial values.
            number = to_number(value)
            if number is not None:
                metrics[normalize_metric_name(key)] = number
            continue
        number = to_number(value)
        if number is not None:
            metrics[normalize_metric_name(key)] = number
    return metrics


def _normalize_fd_financials(
    payload: Dict[str, Any],
    ticker: str,
    fetched_at: str,
) -> List[Dict[str, Any]]:
    block = _records_from_mapping(payload.get("financials")) or payload
    output: List[Dict[str, Any]] = []
    for response_key, statement_type in STATEMENTS:
        rows = find_list(block, (response_key,))
        for row in rows:
            metrics = _metric_values(row)
            if not metrics:
                continue
            output.append({
                "schema_version": 1,
                "source": "financial_datasets",
                "record_type": "financial_statement",
                "ticker": ticker,
                "statement_type": statement_type,
                "period": row.get("fiscal_period") or row.get("report_period") or row.get("period"),
                "report_period": row.get("report_period"),
                "filing_date": row.get("filing_date"),
                "filing_url": row.get("filing_url"),
                "accession_number": row.get("accession_number"),
                "currency": row.get("currency"),
                "fetched_at": fetched_at,
                "metrics": metrics,
                "provider_metadata": {
                    key: json_safe(row.get(key))
                    for key in ("fiscal_period", "period", "report_period", "filing_date", "filing_url", "accession_number")
                    if row.get(key) is not None
                },
            })
    return output


def _normalize_fd_prices(
    payload: Dict[str, Any],
    ticker: str,
    fetched_at: str,
) -> List[Dict[str, Any]]:
    output = []
    for row in find_list(payload, PRICE_KEYS):
        metrics = _metric_values(row)
        if not metrics:
            continue
        output.append({
            "schema_version": 1,
            "source": "financial_datasets",
            "record_type": "price_bar",
            "ticker": ticker,
            "timestamp": row.get("time") or row.get("timestamp") or row.get("date") or row.get("datetime"),
            "currency": row.get("currency"),
            "fetched_at": fetched_at,
            "metrics": metrics,
            "provider_metadata": {
                key: json_safe(row.get(key))
                for key in ("date", "datetime", "timestamp", "interval", "adjusted_close")
                if row.get(key) is not None
            },
        })
    return output


def _normalize_news(
    rows: Iterable[Dict[str, Any]],
    ticker: str,
    source: str,
    fetched_at: str,
) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for row in rows:
        title = str(row.get("title") or row.get("headline") or "").strip()
        summary = str(
            row.get("summary") or row.get("description") or row.get("content") or ""
        ).strip()
        url = row.get("url") or row.get("news_url")
        if not title and not summary:
            continue
        output.append({
            "schema_version": 1,
            "source": source,
            "record_type": "news",
            "ticker": ticker,
            "title": title,
            "text": (title + "\n" + summary).strip(),
            "summary": summary,
            "url": url,
            "published_at": row.get("published_at") or row.get("datetime") or row.get("date") or row.get("created_at"),
            "fetched_at": fetched_at,
            "provider_metadata": json_safe(row),
        })
    return output


def _normalize_quote(
    payload: Dict[str, Any],
    ticker: str,
    source: str,
    fetched_at: str,
) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "source": source,
        "record_type": "quote_snapshot",
        "ticker": ticker,
        "timestamp": payload.get("timestamp") or payload.get("datetime"),
        "currency": payload.get("currency"),
        "fetched_at": fetched_at,
        "metrics": _metric_values(payload),
        "provider_metadata": json_safe(payload),
    }


def collect_financial_datasets(
    client: FinancialDatasetsClient,
    tickers: List[str],
    start_date: str,
    end_date: str,
    include_news: bool,
    include_facts: bool,
) -> tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    if not client.is_configured:
        return records, [{
            "provider": "financial_datasets",
            "ticker": "",
            "operation": "initialize",
            "error": "Skipped: FINANCIAL_DATASETS_API_KEY is not configured.",
        }]

    def run_one(symbol: str, operation: str, callback) -> None:
        try:
            result = callback()
            fetched = utc_now()
            if operation == "prices":
                records.extend(_normalize_fd_prices(result, symbol, fetched))
            elif operation == "financials":
                rows = _normalize_fd_financials(result, symbol, fetched)
                records.extend(rows)
                if not rows:
                    records.append({
                        "schema_version": 1,
                        "source": "financial_datasets",
                        "record_type": "provider_payload",
                        "category": "financials",
                        "ticker": symbol,
                        "fetched_at": fetched,
                        "payload": json_safe(result),
                    })
            elif operation == "news":
                records.extend(_normalize_news(
                    find_list(result, NEWS_KEYS), symbol, "financial_datasets", fetched
                ))
            elif operation == "facts":
                facts = result.get("company_facts") or result
                records.append({
                    "schema_version": 1,
                    "source": "financial_datasets",
                    "record_type": "company_facts",
                    "ticker": symbol,
                    "fetched_at": fetched,
                    "payload": json_safe(facts),
                })
        except Exception as exc:
            errors.append({
                "provider": "financial_datasets",
                "ticker": symbol,
                "operation": operation,
                "error": str(exc),
            })

    for symbol in tickers:
        raw_ticker = fd_ticker(symbol)
        run_one(
            symbol, "prices",
            lambda t=raw_ticker: client.get_prices(t, start_date, end_date, "day"),
        )
        run_one(
            symbol, "financials",
            lambda t=raw_ticker: client.get_financials(t, "annual"),
        )
        if include_news:
            run_one(
                symbol, "news",
                lambda t=raw_ticker: client.get_news(t, limit=20),
            )
        if include_facts:
            run_one(
                symbol, "facts",
                lambda t=raw_ticker: client.get_company_facts(t),
            )
    return records, errors


def collect_longbridge(
    client: LongbridgeClient,
    tickers: List[str],
    start_date: str,
    end_date: str,
    include_news: bool,
) -> tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    if not client.is_configured:
        return records, [{
            "provider": "longbridge_openapi",
            "ticker": "",
            "operation": "initialize",
            "error": "Skipped: Longbridge API credentials are not configured.",
        }]

    for symbol in tickers:
        def run_one(operation: str, callback) -> None:
            try:
                result = callback()
                fetched = utc_now()
                if operation == "quote":
                    records.append(_normalize_quote(result, symbol, "longbridge_openapi", fetched))
                elif operation == "history":
                    for row in result:
                        metrics = _metric_values(row)
                        if metrics:
                            records.append({
                                "schema_version": 1,
                                "source": "longbridge_openapi",
                                "record_type": "price_bar",
                                "ticker": symbol,
                                "timestamp": row.get("timestamp"),
                                "fetched_at": fetched,
                                "metrics": metrics,
                                "provider_metadata": json_safe(row),
                            })
                elif operation == "financials":
                    normalized = normalize_longbridge_financial_reports(result, symbol, fetched)
                    if normalized:
                        records.extend(normalized)
                    else:
                        records.append({
                            "schema_version": 1,
                            "source": "longbridge_openapi",
                            "record_type": "provider_payload",
                            "category": "financials",
                            "ticker": symbol,
                            "fetched_at": fetched,
                            "payload": json_safe(result),
                        })
                elif operation == "news":
                    records.extend(_normalize_news(
                        result, symbol, "longbridge_openapi", fetched
                    ))
            except Exception as exc:
                errors.append({
                    "provider": "longbridge_openapi",
                    "ticker": symbol,
                    "operation": operation,
                    "error": str(exc),
                })

        run_one("quote", lambda s=symbol: client.get_quote(s))
        run_one(
            "history",
            lambda s=symbol: client.get_history(s, start_date, end_date, "1d"),
        )
        run_one("financials", lambda s=symbol: client.get_financials(s, "annual"))
        if include_news:
            run_one("news", lambda s=symbol: client.get_news(s))
    return records, errors


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(json_safe(record), ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickers", default=DEFAULT_TICKERS, help="Comma-separated symbols; Longbridge uses suffixes such as AAPL.US or 700.HK.")
    parser.add_argument("--providers", default="financial_datasets,longbridge", help="Comma-separated subset of financial_datasets,longbridge.")
    parser.add_argument("--start-date", default=(date.today() - timedelta(days=730)).isoformat())
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--output-dir", default=str(ROOT / "data" / "raw" / "finance_api"))
    parser.add_argument("--include-news", action="store_true", help="Also ingest provider news metadata/summaries.")
    parser.add_argument("--include-facts", action="store_true", help="Fetch Financial Datasets company facts (one extra request per ticker).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tickers = [item.strip().upper() for item in args.tickers.split(",") if item.strip()]
    providers = {item.strip().lower() for item in args.providers.split(",") if item.strip()}
    supported = {"financial_datasets", "longbridge"}
    unknown = providers - supported
    if unknown:
        raise SystemExit("Unsupported provider(s): " + ", ".join(sorted(unknown)))
    if not tickers:
        raise SystemExit("Provide at least one ticker.")
    try:
        start = date.fromisoformat(args.start_date)
        end = date.fromisoformat(args.end_date)
    except ValueError as exc:
        raise SystemExit(f"Dates must use YYYY-MM-DD: {exc}") from exc
    if start > end:
        raise SystemExit("--start-date must not be after --end-date.")

    records: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    if "financial_datasets" in providers:
        part, failures = collect_financial_datasets(
            FinancialDatasetsClient(), tickers, start.isoformat(), end.isoformat(),
            args.include_news, args.include_facts,
        )
        records.extend(part)
        errors.extend(failures)
    if "longbridge" in providers:
        part, failures = collect_longbridge(
            LongbridgeClient(), tickers, start.isoformat(), end.isoformat(),
            args.include_news,
        )
        records.extend(part)
        errors.extend(failures)

    output_dir = Path(args.output_dir).resolve()
    records_path = output_dir / "records.jsonl"
    manifest_path = output_dir / "manifest.json"
    write_jsonl(records_path, records)
    manifest = {
        "schema_version": 1,
        "created_at": utc_now(),
        "tickers": tickers,
        "providers_requested": sorted(providers),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "include_news": bool(args.include_news),
        "include_facts": bool(args.include_facts),
        "record_count": len(records),
        "record_counts_by_source": dict(Counter(r.get("source", "unknown") for r in records)),
        "record_counts_by_type": dict(Counter(r.get("record_type", "unknown") for r in records)),
        "errors": errors,
        "records_file": str(records_path),
        "license_notice": (
            "Local research pipeline only. Review each provider's current license, "
            "terms, attribution and model-training permissions before using or redistributing data."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "records": len(records),
        "record_counts_by_source": manifest["record_counts_by_source"],
        "record_counts_by_type": manifest["record_counts_by_type"],
        "errors": len(errors),
        "records_file": str(records_path),
        "manifest_file": str(manifest_path),
    }, ensure_ascii=False, indent=2))
    return 0 if records else 2


if __name__ == "__main__":
    raise SystemExit(main())
