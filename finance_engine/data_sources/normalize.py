"""Safe serialization and normalization helpers for external financial data."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import re
from typing import Any, Dict, Iterable, List, Optional


_METRIC_ALIASES = {
    "revenue": "revenue",
    "total_rev": "revenue",
    "total_revenue": "revenue",
    "revenue_total": "revenue",
    "rev": "revenue",
    "operating_revenue": "revenue",
    "operatingrevenue": "revenue",
    "营业收入": "revenue",
    "营业收入usd": "revenue",
    "net_income": "net_income",
    "net_profit": "net_income",
    "net_income_loss": "net_income",
    "net_profit_common_stock": "net_income",
    "netprofit": "net_income",
    "净利润": "net_income",
    "eps": "eps",
    "earnings_per_share": "eps",
    "earnings_per_share_diluted": "eps",
    "basic_eps": "eps",
    "diluted_eps": "eps",
    "每股收益": "eps",
    "roe": "roe",
    "roedf": "roe",
    "return_on_equity": "roe",
    "operating_income": "operating_income",
    "operatingincome": "operating_income",
    "营业利润": "operating_income",
    "cost_of_revenue": "cost_of_revenue",
    "cost_rev": "cost_of_revenue",
    "营业成本": "cost_of_revenue",
    "gross_profit": "gross_profit",
    "毛利润": "gross_profit",
    "total_assets": "total_assets",
    "总资产": "total_assets",
    "total_liabilities": "total_liabilities",
    "total_debts": "total_liabilities",
    "total_debt": "total_debt",
    "shareholders_equity": "shareholders_equity",
    "total_equity": "shareholders_equity",
    "股东权益": "shareholders_equity",
    "operating_cash_flow": "operating_cash_flow",
    "operating_cashflow": "operating_cash_flow",
    "free_cash_flow": "free_cash_flow",
    "cash_and_equivalents": "cash_and_equivalents",
    "market_cap": "market_cap",
    "pe_ratio": "pe_ratio",
    "pe_ttm": "pe_ratio",
    "pb_ratio": "pb_ratio",
}


def json_safe(value: Any) -> Any:
    """Convert SDK/API values into JSON-compatible values without losing metadata."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item) for item in value]
    if is_dataclass(value):
        return json_safe(asdict(value))

    for method_name in ("model_dump", "to_dict", "dict", "_asdict"):
        method = getattr(value, method_name, None)
        if callable(method):
            try:
                mapped = method()
                if isinstance(mapped, dict):
                    return json_safe(mapped)
            except Exception:
                pass

    fields = getattr(value, "__dict__", None)
    if isinstance(fields, dict) and fields:
        return json_safe(fields)

    # Some SDK response objects expose fields as properties/slots.
    candidate_names = (
        "symbol", "last_done", "prev_close", "prev_close_price", "open", "high", "low",
        "close", "volume", "timestamp", "turnover", "currency", "list",
        "id", "title", "description", "url", "published_at", "datetime",
        "report_period", "fiscal_period", "year", "value", "yoy",
        "indicators", "accounts", "values", "field", "name", "period",
        "filing_url", "filing_date", "accession_number", "revenue",
        "net_income", "eps", "roe", "open_interest",
    )
    mapped = {}
    for name in candidate_names:
        try:
            item = getattr(value, name)
        except Exception:
            continue
        if callable(item):
            continue
        mapped[name] = json_safe(item)
    if mapped:
        return mapped
    return str(value)


def to_number(value: Any) -> Optional[float]:
    """Parse a finite numeric value; return None for labels, NaN and missing data."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if not value or value in {"-", "—", "N/A", "null", "None"}:
            return None
        if value.endswith("%"):
            value = value[:-1].strip()
    try:
        result = float(value)
    except (TypeError, ValueError, InvalidOperation):
        return None
    if result != result or result in (float("inf"), float("-inf")):
        return None
    return result


def normalize_metric_name(name: Any) -> str:
    """Map commonly used English/Chinese provider field names to canonical keys."""
    raw = str(name or "").strip()
    compact = re.sub(r"[\s()./%-]+", "", raw).lower()
    underscored = re.sub(r"[^a-z0-9_]+", "_", raw.lower()).strip("_")
    for candidate in (raw.lower(), compact, underscored):
        if candidate in _METRIC_ALIASES:
            return _METRIC_ALIASES[candidate]
    return underscored or "unknown_metric"


def find_list(payload: Any, preferred_keys: Iterable[str]) -> List[dict]:
    """Find a list of row-like dictionaries inside common provider response envelopes."""
    payload = json_safe(payload)
    preferred = {str(key).lower() for key in preferred_keys}

    def walk(node: Any) -> Optional[List[dict]]:
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key).lower() in preferred and isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            for value in node.values():
                found = walk(value)
                if found is not None:
                    return found
        elif isinstance(node, list):
            for value in node:
                found = walk(value)
                if found is not None:
                    return found
        return None

    return walk(payload) or []


def normalize_statement_kind(name: Any) -> str:
    text = str(name or "").lower().replace("-", "_").replace(" ", "_")
    compact = text.replace("_", "")
    if compact in {"is", "income", "incomestatement", "incomestatements", "isdata"}:
        return "income_statement"
    if compact in {"bs", "balancesheet", "balancesheets", "bsdata"}:
        return "balance_sheet"
    if compact in {"cf", "cashflow", "cashflows", "cashflowstatement", "cfdata"}:
        return "cash_flow_statement"
    if "income" in compact or compact in {"is", "i_s"}:
        return "income_statement"
    if "balance" in compact or compact in {"bs", "b_s"}:
        return "balance_sheet"
    if "cashflow" in compact or compact in {"cf", "c_f"}:
        return "cash_flow_statement"
    return "financial_statement"


def _normalize_report_date(value: Any) -> Optional[str]:
    """Convert Unix seconds/milliseconds or ISO dates to a stable YYYY-MM-DD."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) or (
        isinstance(value, str) and value.strip().isdigit()
    ):
        try:
            number = float(value)
            if number > 10_000_000_000:
                number /= 1000.0
            return datetime.fromtimestamp(number, tz=timezone.utc).date().isoformat()
        except (OverflowError, OSError, ValueError):
            return None
    text = str(value).strip()
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return text or None


def normalize_longbridge_financial_reports(
    payload: Any,
    ticker: str,
    fetched_at: str,
) -> List[Dict[str, Any]]:
    """Flatten Longbridge FinancialReports indicators into period-keyed metric records."""
    root = json_safe(payload)
    if isinstance(root, dict) and "list" in root:
        root = root["list"]

    grouped: Dict[tuple, Dict[str, Any]] = {}

    def visit(node: Any, node_name: str = "") -> None:
        if isinstance(node, dict):
            indicators = node.get("indicators")
            if isinstance(indicators, list):
                statement_type = normalize_statement_kind(node_name)
                for indicator in indicators:
                    if not isinstance(indicator, dict):
                        continue
                    raw_metric = indicator.get("field") or indicator.get("indicator_name") or indicator.get("title") or indicator.get("name")
                    accounts = indicator.get("accounts", [])
                    if not isinstance(accounts, list):
                        continue
                    for account in accounts:
                        if not isinstance(account, dict):
                            continue
                        # Longbridge places the canonical financial field on
                        # each account, while the parent indicator title may be
                        # a display group (for example, "profitability").
                        account_metric = (
                            account.get("field")
                            or account.get("name")
                            or raw_metric
                        )
                        metric = normalize_metric_name(account_metric)
                        currency = account.get("currency") or indicator.get("currency")
                        values = account.get("values", [])
                        if not isinstance(values, list):
                            continue
                        for item in values:
                            if not isinstance(item, dict):
                                continue
                            year = item.get("year")
                            period = item.get("period") or (
                                f"FY{year}" if year is not None else item.get("report_period")
                            )
                            if not period:
                                continue
                            key = (str(ticker), statement_type, str(period), str(currency or ""))
                            record = grouped.setdefault(
                                key,
                                {
                                    "schema_version": 1,
                                    "source": "longbridge_openapi",
                                    "record_type": "financial_statement",
                                    "ticker": str(ticker),
                                    "statement_type": statement_type,
                                    "period": str(period),
                                    "report_period": _normalize_report_date(item.get("fp_end") or item.get("report_period")),
                                    "fiscal_year": year,
                                    "currency": currency,
                                    "fetched_at": fetched_at,
                                    "metrics": {},
                                    "metrics_yoy": {},
                                },
                            )
                            number = to_number(item.get("value"))
                            if number is not None:
                                record["metrics"][metric] = number
                            yoy = to_number(item.get("yoy"))
                            if yoy is not None:
                                record["metrics_yoy"][metric] = yoy
                return
            for key, value in node.items():
                visit(value, str(key))
        elif isinstance(node, list):
            for value in node:
                visit(value, node_name)

    visit(root)
    return [
        row for row in grouped.values()
        if row["metrics"]
    ]
