"""Build small, period-grounded SFT examples from ingested financial statements.

Use only data whose license permits the intended fine-tuning. This builder avoids
training on live quotes/news as facts and excludes observations when providers
disagree on the same ticker, period, statement and metric.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finance_engine.data_sources.normalize import to_number


METRIC_LABELS = {
    "revenue": "revenue",
    "net_income": "net income",
    "operating_income": "operating income",
    "gross_profit": "gross profit",
    "total_assets": "total assets",
    "total_liabilities": "total liabilities",
    "total_debt": "total debt",
    "shareholders_equity": "shareholders' equity",
    "operating_cash_flow": "cash flow from operations",
    "free_cash_flow": "free cash flow",
    "eps": "earnings per share (EPS)",
}
STATEMENT_LABELS = {
    "income_statement": "income statement",
    "balance_sheet": "balance sheet",
    "cash_flow_statement": "cash-flow statement",
}


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}: {exc}") from exc
            if isinstance(row, dict):
                records.append(row)
    return records


def _value_fingerprint(value: float) -> str:
    return f"{value:.8g}"


def _format_value(value: float, metric: str) -> str:
    if metric == "eps":
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:,.4f}".rstrip("0").rstrip(".")


def build_sft_examples(
    records: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    observations: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("record_type") != "financial_statement":
            continue
        ticker = str(record.get("ticker") or "").strip().upper()
        statement_type = str(record.get("statement_type") or "")
        period = str(record.get("period") or record.get("report_period") or "").strip()
        metrics = record.get("metrics")
        if not ticker or not period or not isinstance(metrics, dict):
            continue
        for metric, raw_value in metrics.items():
            if metric not in METRIC_LABELS:
                continue
            value = to_number(raw_value)
            if value is None:
                continue
            key = (ticker, statement_type, period, metric)
            observations[key].append({
                "value": value,
                "source": str(record.get("source") or "unknown"),
                "currency": str(record.get("currency") or ""),
                "report_period": str(record.get("report_period") or ""),
                "filing_url": str(record.get("filing_url") or ""),
                "accession_number": str(record.get("accession_number") or ""),
                "fetched_at": str(record.get("fetched_at") or ""),
            })

    examples: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []
    seen = set()
    for (ticker, statement_type, period, metric), items in sorted(observations.items()):
        distinct_values = {_value_fingerprint(item["value"]) for item in items}
        if len(distinct_values) > 1:
            conflicts.append({
                "ticker": ticker,
                "statement_type": statement_type,
                "period": period,
                "metric": metric,
                "observations": [
                    {"source": item["source"], "value": item["value"]}
                    for item in items
                ],
                "reason": "Provider values disagree; omitted from SFT examples.",
            })
            continue

        value = items[0]["value"]
        sources = sorted({item["source"] for item in items})
        currencies = sorted({item["currency"] for item in items if item["currency"]})
        currency = currencies[0] if len(currencies) == 1 else ""
        dates = sorted({item["report_period"] for item in items if item["report_period"]})
        report_date = dates[0] if len(dates) == 1 else ""
        filing_urls = sorted({item["filing_url"] for item in items if item["filing_url"]})
        accession_numbers = sorted({item["accession_number"] for item in items if item["accession_number"]})
        metric_label = METRIC_LABELS[metric]
        statement_label = STATEMENT_LABELS.get(statement_type, "financial statement")
        value_text = _format_value(value, metric)
        if metric == "eps":
            amount = f"{value_text} {currency + ' ' if currency else ''}per share"
        else:
            amount = f"{currency + ' ' if currency else ''}{value_text}"

        prompt = (
            f"For {ticker}, what {metric_label} was reported for {period}? "
            f"Use only the cited historical {statement_label}; do not infer a current value."
        )
        source_text = ", ".join(sources)
        citation = filing_urls[0] if len(filing_urls) == 1 else source_text
        completion = (
            f"The reported {metric_label} for {ticker} in {period} was {amount}. "
        )
        if report_date:
            completion += f"The reporting date was {report_date}. "
        completion += (
            f"Source: {source_text}"
            + (f" ({citation})" if citation and citation != source_text else "")
            + ". This is historical reported data, not a live quote or forecast."
        )
        fingerprint = hashlib.sha256(
            (prompt.strip().lower() + "\n" + completion.strip().lower()).encode("utf-8")
        ).hexdigest()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        examples.append({
            "prompt": prompt,
            "completion": completion,
            "task_type": "provider_grounded_financial_fact",
            "ticker": ticker,
            "statement_type": statement_type,
            "period": period,
            "metric": metric,
            "provider_sources": sources,
            "source_urls": filing_urls,
            "source_accession_numbers": accession_numbers,
            "source_fetched_at": sorted({item["fetched_at"] for item in items if item["fetched_at"]}),
        })

    return examples, conflicts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" / "raw" / "finance_api" / "records.jsonl"),
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "data" / "sft_v3_work" / "provider_finance" / "finance_sft.jsonl"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    if not input_path.is_file():
        raise SystemExit(
            f"Input corpus not found: {input_path}. Run scripts/ingest_finance_api_data.py first."
        )

    records = read_jsonl(input_path)
    examples, conflicts = build_sft_examples(records)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as stream:
        for example in examples:
            stream.write(json.dumps(example, ensure_ascii=False) + "\n")

    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": str(input_path.resolve()),
        "output": str(output_path.resolve()),
        "input_record_count": len(records),
        "sft_example_count": len(examples),
        "examples_by_provider_source": dict(Counter(
            source
            for example in examples
            for source in example.get("provider_sources", [])
        )),
        "examples_by_statement_type": dict(Counter(
            example.get("statement_type", "unknown") for example in examples
        )),
        "conflicting_metric_count": len(conflicts),
        "conflicts": conflicts,
        "policy": (
            "Historical statement facts only. Provider disagreements are excluded. "
            "Review licensing and temporal/company holdouts before full training."
        ),
    }
    manifest_path = output_path.with_name("finance_sft_manifest.json")
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "input_records": len(records),
        "sft_examples": len(examples),
        "conflicts_excluded": len(conflicts),
        "output": str(output_path),
        "manifest": str(manifest_path),
    }, ensure_ascii=False, indent=2))
    return 0 if examples else 2


if __name__ == "__main__":
    raise SystemExit(main())
