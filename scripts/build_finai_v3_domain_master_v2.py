from pathlib import Path
import json
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_merged.jsonl"
)

OUT = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_domain_master_v2.jsonl"
)

MANIFEST = (
    ROOT
    / "data"
    / "manifests"
    / "finai_v3_domain_master_v2_manifest.json"
)


KEEP_SOURCES = {
    "FinQA",
    "TAT-QA",
    "FinAI-Intent-Seed",
    "FinAI-Contrastive-Synthetic",
}


FINANCE_TERMS = re.compile(
    r"""
    (
        bank|banking|loan|mortgage|credit|debit|
        payment|payments|transaction|transactions|
        account|accounts|investment|investing|investor|
        stock|stocks|share|shares|bond|bonds|
        equity|equities|dividend|dividends|
        portfolio|mutual\s+fund|asset|assets|
        liability|liabilities|revenue|revenues|
        profit|profits|loss|losses|income|expense|
        expenses|cash\s+flow|balance\s+sheet|
        income\s+statement|annual\s+report|
        financial\s+statement|accounting|
        tax|taxes|taxation|interest|interest\s+rate|
        inflation|deflation|market|markets|
        capital\s+market|valuation|forex|currency|
        currencies|insurance|premium|claim|claims|
        pension|retirement|deposit|deposits|
        withdrawal|withdrawals|atm|transfer|transfers|
        wallet|merchant|refund|fraud|kyc|emi|
        beneficiary|upi|rupee|rupees|dollar|dollars|
        euro|euros|pound|pounds|yen|gold|silver|
        commodity|commodities|treasury|yield|
        fintech|financial\s+technology|
        interest|principal|installment|instalment|
        savings|saving|budget|debt|dividend|
        earnings|financing|funding|capital|
        shareholder|shareholder|cash|invoice|billing|
        premium|policy|underwriting|credit\s+score|
        interest\s+expense|operating\s+income|
        gross\s+profit|net\s+income|net\s+debt|
        accounts\s+receivable|accounts\s+payable|
        monetary|fiscal|economy|economic
    |
        金融|银行|贷款|信用|支付|交易|账户|投资|
        股票|债券|利率|税|保险|养老金|基金|
        资产|负债|收入|利润|亏损|股息|货币|
        资本市场
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


STRONG_NONFINANCE = re.compile(
    r"""
    (
        vaccine|vaccination|football|soccer|basketball|
        baseball|cricket|polynomial|exponential\s+equation|
        random\s+numbers|array\s+of\s+size|programming|
        python\s+code|java\s+code|javascript|
        subordinating\s+clause|grammar|sentence\s+using|
        rewrite\s+the\s+sentence|space\s+station|
        celestial\s+body|astronomy|planetary|
        chemistry|biology|physics\s+experiment|
        recipe|cooking|romantic\s+relationship|
        relationship\s+advice|memorial\s+service|
        how\s+many\s+people\s+died|president|
        plato|socrates|philosophy|space\s+exploration|
        street\s+address|phone\s+number|postal\s+code
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


FINANCE_TASK_TYPES = {
    "financial_instruction",
    "financial_reasoning",
    "financial_table_reasoning",
    "numeric_reasoning",
    "risk_analysis",
}


TEXT_TASK_TYPES = {
    "qa",
    "qa_with_context",
    "qa_conversation",
    "sentiment_analysis",
    "topic_classification",
    "ner_sentiment_analysis",
}


def relevant(row):

    source = str(
        row.get(
            "source_dataset",
            ""
        )
    )

    task = str(
        row.get(
            "task_type",
            ""
        )
    )

    user = str(
        row.get(
            "user",
            ""
        )
    )

    assistant = str(
        row.get(
            "assistant",
            ""
        )
    )

    text = user + "\n" + assistant

    # Domain-specific datasets are retained.
    if source in KEEP_SOURCES:
        return True, "domain_specific_source"

    finance_match = bool(
        FINANCE_TERMS.search(text)
    )

    nonfinance_match = bool(
        STRONG_NONFINANCE.search(text)
    )

    # If the record contains a strong obvious non-financial
    # signal and no financial signal, remove it.
    if nonfinance_match and not finance_match:
        return False, "obvious_non_financial"

    # Financial task types are retained unless clearly
    # identified as unrelated above.
    if task in FINANCE_TASK_TYPES:
        return True, "finance_task_type"

    # Generic QA/sentiment/topic records are retained only
    # when there is actual financial evidence.
    if task in TEXT_TASK_TYPES:
        if finance_match:
            return True, "financial_signal"

        return False, "generic_task_without_financial_signal"

    # Other records are retained when they contain finance
    # evidence.
    if finance_match:
        return True, "financial_signal"

    # Conservative fallback:
    # keep unknown records rather than deleting them merely
    # because the keyword dictionary is incomplete.
    return True, "unknown_task_conservative_keep"


def main():

    print("=" * 72)
    print("FINAI-V3 CORRECTED DOMAIN MASTER BUILD")
    print("=" * 72)

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Missing input:\n{INPUT}"
        )

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    total = 0
    kept = 0
    removed = 0

    reasons = Counter()
    sources_before = Counter()
    sources_after = Counter()

    with INPUT.open(
        "r",
        encoding="utf-8"
    ) as src, OUT.open(
        "w",
        encoding="utf-8"
    ) as dst:

        for line in src:

            if not line.strip():
                continue

            row = json.loads(line)

            total += 1

            source = str(
                row.get(
                    "source_dataset",
                    "unknown"
                )
            )

            sources_before[source] += 1

            keep, reason = relevant(row)

            reasons[reason] += 1

            if keep:
                dst.write(
                    json.dumps(
                        row,
                        ensure_ascii=False
                    ) + "\n"
                )

                kept += 1
                sources_after[source] += 1

            else:
                removed += 1

    manifest = {
        "dataset": "FinAI-V3 corrected domain master",
        "input_records": total,
        "kept_records": kept,
        "removed_records": removed,
        "reasons": dict(reasons),
        "sources_before": dict(sources_before),
        "sources_after": dict(sources_after),
        "policy": (
            "Filter master before train/validation/test split. "
            "Domain-specific FinAI, FinQA and TAT-QA records "
            "are preserved. Finance-Instruct and FinMix use "
            "source-aware and task-aware filtering."
        ),
        "output": str(OUT),
    }

    MANIFEST.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("INPUT:", total)
    print("KEPT:", kept)
    print("REMOVED:", removed)

    print()
    print("KEEP %:",
          round(
              kept / total * 100,
              2
          ) if total else 0)

    print()
    print("REASONS:")

    for key, value in reasons.most_common():
        print(
            f"  {key}: {value}"
        )

    print()
    print("SOURCES AFTER FILTER:")

    for key, value in sources_after.most_common():
        print(
            f"  {key}: {value}"
        )

    print()
    print("[OK] Master:", OUT)
    print("[OK] Manifest:", MANIFEST)

    print("=" * 72)
    print("CORRECTED DOMAIN MASTER COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
