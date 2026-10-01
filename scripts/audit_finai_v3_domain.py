from pathlib import Path
import json
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "training_ready"
    / "train.jsonl"
)

FINANCIAL_TERMS = re.compile(
    r"\b("
    r"bank|banking|loan|credit|payment|payments|"
    r"transaction|account|investment|investing|stock|stocks|"
    r"bond|bonds|tax|interest|mortgage|insurance|"
    r"upi|card|refund|fraud|kyc|emi|debit|transfer|"
    r"money|cash|wallet|merchant|balance|saving|savings|"
    r"budget|mutual fund|portfolio|deposit|withdrawal|"
    r"atm|beneficiary|installment|forex|currency|asset|"
    r"liability|revenue|profit|loss|income|expense|debt|"
    r"equity|dividend|accounting|invoice|billing|"
    r"financial|finance"
    r")\b",
    re.IGNORECASE,
)

FINAI_SOURCES = {
    "FinAI-Intent-Seed",
    "FinAI-Contrastive-Synthetic",
}


def extract_user_text(prompt):
    marker = "\nUSER:\n"

    if marker in prompt:
        return prompt.split(
            marker,
            1
        )[1].strip()

    return prompt.strip()


def extract_completion_text(completion):
    marker = "\nRESPONSE:"

    if marker in completion:
        return completion.split(
            marker,
            1
        )[1].strip()

    return completion.strip()


def main():

    print("=" * 72)
    print("FINAI-V3 CORRECTED DOMAIN QUALITY AUDIT")
    print("=" * 72)

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{INPUT}"
        )

    total = 0
    financial_user = 0
    financial_completion = 0
    financial_either = 0
    candidates = []

    source_counts = Counter()
    candidate_by_source = Counter()

    with INPUT.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line_number, line in enumerate(
            f,
            start=1
        ):

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

            source_counts[source] += 1

            prompt = str(
                row.get(
                    "prompt",
                    ""
                )
            )

            completion = str(
                row.get(
                    "completion",
                    ""
                )
            )

            # IMPORTANT:
            # Remove the universal FinAI system prompt
            # from the domain check.
            user_text = extract_user_text(
                prompt
            )

            completion_text = (
                extract_completion_text(
                    completion
                )
            )

            user_match = bool(
                FINANCIAL_TERMS.search(
                    user_text
                )
            )

            completion_match = bool(
                FINANCIAL_TERMS.search(
                    completion_text
                )
            )

            if user_match:
                financial_user += 1

            if completion_match:
                financial_completion += 1

            is_financial = (
                user_match
                or completion_match
                or source in FINAI_SOURCES
            )

            if is_financial:
                financial_either += 1

            else:
                candidate_by_source[
                    source
                ] += 1

                if len(candidates) < 30:
                    candidates.append({
                        "line": line_number,
                        "source": source,
                        "user": user_text[:700],
                        "completion":
                            completion_text[:500],
                    })

    print()
    print("TOTAL:", total)

    print(
        "USER FINANCIAL MATCH:",
        financial_user
    )

    print(
        "COMPLETION FINANCIAL MATCH:",
        financial_completion
    )

    print(
        "FINANCIAL-LIKELY:",
        financial_either
    )

    print(
        "NON-FINANCIAL-CANDIDATES:",
        total - financial_either
    )

    if total:
        print()
        print(
            "USER MATCH %:",
            round(
                financial_user / total * 100,
                2
            )
        )

        print(
            "NON-FINANCIAL CANDIDATE %:",
            round(
                (total - financial_either)
                / total
                * 100,
                2
            )
        )

    print()
    print("SOURCE COUNTS:")

    for source, count in (
        source_counts.most_common()
    ):
        print(
            f"  {source}: {count}"
        )

    print()
    print(
        "NON-FINANCIAL CANDIDATES BY SOURCE:"
    )

    if not candidate_by_source:
        print("  None")

    for source, count in (
        candidate_by_source.most_common()
    ):
        print(
            f"  {source}: {count}"
        )

    print()
    print(
        "SAMPLE NON-FINANCIAL CANDIDATES:"
    )

    if not candidates:
        print("  None")

    for i, item in enumerate(
        candidates,
        start=1
    ):

        print()
        print(
            f"--- SAMPLE {i} ---"
        )

        print(
            "LINE:",
            item["line"]
        )

        print(
            "SOURCE:",
            item["source"]
        )

        print(
            "USER:",
            item["user"]
        )

        print(
            "COMPLETION:",
            item["completion"]
        )

    print()
    print("=" * 72)
    print("CORRECTED DOMAIN AUDIT COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
