from pathlib import Path
import json
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = ROOT / "data" / "sft_v3_work" / "final_split"
OUTPUT_DIR = ROOT / "data" / "sft_v3_work" / "domain_filtered"

MANIFEST = ROOT / "data" / "manifests" / "finai_v3_domain_filter_manifest.json"

KEEP_SOURCES = {
    "FinAI-Intent-Seed",
    "FinAI-Contrastive-Synthetic",
    "FinQA",
    "TAT-QA",
}

FILTER_SOURCES = {
    "Finance-Instruct-500k",
    "FinMix",
}


FINANCE_TERMS = re.compile(
    r"""
    (
        finance|financial|bank|banking|loan|mortgage|credit|debit|
        payment|payments|transaction|transactions|account|accounts|
        investment|investing|investor|stock|stocks|share|shares|
        bond|bonds|equity|equities|dividend|dividends|
        portfolio|mutual\s+fund|funds|asset|assets|liability|liabilities|
        revenue|revenues|profit|profits|loss|losses|income|expenses|
        expense|earnings|cash\s+flow|balance\s+sheet|income\s+statement|
        annual\s+report|financial\s+statement|accounting|
        tax|taxes|taxation|interest|interest\s+rate|
        inflation|deflation|market|markets|capital\s+market|
        market\s+cap|valuation|forex|currency|currencies|
        insurance|premium|claim|claims|pension|retirement|
        deposit|deposits|withdrawal|withdrawals|atm|
        transfer|transfers|wallet|merchant|refund|fraud|kyc|emi|
        beneficiary|upi|rupee|rupees|dollar|dollars|euro|euros|
        pound|pounds|yen|gold|silver|commodity|commodities|
        treasury|bond\s+yield|yield|rate|rates|fintech|
        financial\s+technology|bank\s+account
    |
        金融|银行|贷款|信用|支付|交易|账户|投资|股票|债券|利率|
        税|保险|养老金|基金|资产|负债|收入|利润|亏损|股息|货币|
        资本市场
    |
        finanzas|financiero|banco|banca|préstamo|crédito|pago|
        transacción|cuenta|inversión|acciones|bonos|impuestos|
        interés|seguro|mercado|ingresos|ganancias|pérdidas|
        activos|pasivos|dividendos
    |
        banque|bancaire|prêt|crédit|paiement|transaction|compte|
        investissement|actions|obligations|impôt|intérêt|assurance|
        marché|revenus|bénéfice|perte|actifs|passifs|dividende
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


# Strong signals that the example is usually unrelated
# to financial-domain training.
NON_FINANCE_TERMS = re.compile(
    r"""
    (
        vaccine|vaccination|doses?\s+of\s+the\s+vaccine|
        football|soccer|basketball|baseball|
        mothers?\s+day|memorial\s+to|
        polynomial|exponential\s+equation|
        random\s+numbers|array\s+of\s+size|
        space\s+station|celestial\s+body|astronomy|
        subordinating\s+clause|grammar|
        sentence\s+using|rewrite\s+the\s+sentence|
        describe\s+a\s+space\s+station|
        chemistry|biology|physics\s+experiment|
        recipe|cooking|relationship\s+advice|
        romantic\s+relationship|
        how\s+many\s+people\s+died|
        who\s+is\s+the\s+president|
        memorial\s+service
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def extract_user(prompt):
    marker = "\nUSER:\n"

    if marker in prompt:
        return prompt.split(
            marker,
            1
        )[1].strip()

    return prompt.strip()


def extract_completion(completion):
    marker = "\nRESPONSE:"

    if marker in completion:
        return completion.split(
            marker,
            1
        )[1].strip()

    return completion.strip()


def financial_relevance(row):

    source = str(
        row.get(
            "source_dataset",
            ""
        )
    )

    if source in KEEP_SOURCES:
        return True, "domain_specific_source"

    if source not in FILTER_SOURCES:
        return True, "unknown_source_kept"

    prompt = extract_user(
        str(row.get("prompt", ""))
    )

    completion = extract_completion(
        str(row.get("completion", ""))
    )

    text = (
        prompt
        + "\n"
        + completion
    )

    finance_match = bool(
        FINANCE_TERMS.search(text)
    )

    nonfinance_match = bool(
        NON_FINANCE_TERMS.search(text)
    )

    # Strong finance evidence wins.
    if finance_match:
        return True, "financial_signal"

    # Strong obvious off-domain signal.
    if nonfinance_match:
        return False, "obvious_non_financial"

    # Currency / percentage / financial-number structures.
    if re.search(
        r"[$€£¥₹]\s*[\d,]+",
        text
    ):
        return True, "currency_signal"

    if re.search(
        r"\b\d+(?:\.\d+)?\s*%",
        text
    ):
        return True, "percentage_signal"

    # Financial reporting style.
    if re.search(
        r"\b"
        r"(revenue|income|expense|profit|loss|sales|"
        r"asset|liability|cash|debt|equity)"
        r"\b",
        text,
        re.IGNORECASE,
    ):
        return True, "financial_accounting_signal"

    return False, "no_financial_signal"


def write_jsonl(path, rows):
    with path.open(
        "w",
        encoding="utf-8"
    ) as f:

        for row in rows:
            f.write(
                json.dumps(
                    row,
                    ensure_ascii=False
                )
                + "\n"
            )


def process_file(filename):

    input_path = INPUT_DIR / filename
    output_path = OUTPUT_DIR / filename

    kept = []
    reasons = Counter()

    total = 0
    kept_count = 0
    removed_count = 0

    with input_path.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if not line.strip():
                continue

            row = json.loads(line)

            total += 1

            keep, reason = financial_relevance(
                row
            )

            reasons[reason] += 1

            if keep:
                kept.append(row)
                kept_count += 1
            else:
                removed_count += 1

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    write_jsonl(
        output_path,
        kept
    )

    print()
    print("=" * 72)
    print("FILE:", filename)
    print("INPUT:", total)
    print("KEPT:", kept_count)
    print("REMOVED:", removed_count)

    print()
    print("REASONS:")
    for reason, count in reasons.most_common():
        print(
            f"  {reason}: {count}"
        )

    print(
        "OUTPUT:",
        output_path
    )


def main():

    print("=" * 72)
    print("FINAI-V3 DOMAIN FILTER")
    print("=" * 72)

    for filename in (
        "train.jsonl",
        "validation.jsonl",
        "test.jsonl",
    ):
        process_file(filename)

    print()
    print("=" * 72)
    print("DOMAIN FILTER COMPLETE")
    print("=" * 72)
    print(
        "IMPORTANT: Original split files were NOT modified."
    )


if __name__ == "__main__":
    main()
