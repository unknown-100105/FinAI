from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "sft_final" / "train.jsonl"
TAXONOMY = ROOT / "data" / "intent_taxonomy.json"
OUTPUT = ROOT / "evaluation" / "sft_balance_report.json"


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"[WARN] Invalid JSON at {path}:{line_no}: {exc}")
    return records


def main() -> None:
    if not DATASET.exists():
        raise FileNotFoundError(f"Missing dataset: {DATASET}")

    if not TAXONOMY.exists():
        raise FileNotFoundError(f"Missing taxonomy: {TAXONOMY}")

    records = load_jsonl(DATASET)

    with TAXONOMY.open("r", encoding="utf-8") as f:
        taxonomy = json.load(f)

    taxonomy_names = []
    taxonomy_by_name: dict[str, dict] = {}

    for item in taxonomy:
        name = item.get("intent") or item.get("name")
        if name:
            taxonomy_names.append(name)
            taxonomy_by_name[name] = item

    intent_counts = Counter()
    language_counts: dict[str, Counter] = defaultdict(Counter)
    tool_counts: dict[str, Counter] = defaultdict(Counter)
    risk_counts: dict[str, Counter] = defaultdict(Counter)
    lengths: dict[str, list[int]] = defaultdict(list)
    prompt_fingerprints: dict[str, Counter] = defaultdict(Counter)

    for record in records:
        intent = record.get("intent") or "<MISSING_INTENT>"
        language = record.get("language") or "<MISSING_LANGUAGE>"
        tool = record.get("tool_name") or "none"
        risk = record.get("risk_level") or "<MISSING_RISK>"

        prompt = (
            record.get("question")
            or record.get("prompt")
            or record.get("input")
            or ""
        )

        intent_counts[intent] += 1
        language_counts[intent][language] += 1
        tool_counts[intent][tool] += 1
        risk_counts[intent][risk] += 1
        lengths[intent].append(len(prompt.strip()))

        normalized = " ".join(prompt.lower().split())
        if normalized:
            prompt_fingerprints[intent][normalized] += 1

    all_dataset_intents = set(intent_counts)
    taxonomy_intents = set(taxonomy_names)

    zero_example = sorted(taxonomy_intents - all_dataset_intents)

    extra_dataset_intents = sorted(all_dataset_intents - taxonomy_intents)

    underrepresented = sorted(
        (name, intent_counts.get(name, 0))
        for name in taxonomy_names
        if 0 < intent_counts.get(name, 0) < 100
    )

    duplicate_rates = {}

    for intent, counts in prompt_fingerprints.items():
        total = sum(counts.values())
        duplicates = sum(v - 1 for v in counts.values() if v > 1)
        duplicate_rates[intent] = (
            duplicates / total if total else 0.0
        )

    report = {
        "dataset": str(DATASET),
        "taxonomy": str(TAXONOMY),
        "dataset_records": len(records),
        "taxonomy_intents": len(taxonomy_intents),
        "dataset_intents": len(all_dataset_intents),
        "zero_example_intents": zero_example,
        "extra_dataset_intents": extra_dataset_intents,
        "underrepresented_intents": [
            {"intent": name, "count": count}
            for name, count in underrepresented
        ],
        "intent_stats": {},
    }

    for intent in sorted(taxonomy_intents | all_dataset_intents):
        meta = taxonomy_by_name.get(intent, {})

        report["intent_stats"][intent] = {
            "description": meta.get("description", ""),
            "category": meta.get("category", ""),
            "taxonomy_requires_tool": meta.get("requires_tool"),
            "examples": intent_counts.get(intent, 0),
            "languages": dict(language_counts.get(intent, {})),
            "tools": dict(tool_counts.get(intent, {})),
            "risk_levels": dict(risk_counts.get(intent, {})),
            "avg_prompt_length": (
                round(mean(lengths[intent]), 2)
                if lengths.get(intent)
                else 0
            ),
            "duplicate_rate": round(
                duplicate_rates.get(intent, 0.0), 4
            ),
        }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=" * 72)
    print("FINAI SFT DATASET BALANCE ANALYSIS")
    print("=" * 72)
    print(f"Dataset records       : {len(records)}")
    print(f"Taxonomy intents      : {len(taxonomy_intents)}")
    print(f"Dataset intents       : {len(all_dataset_intents)}")
    print(f"Zero-example intents  : {len(zero_example)}")
    print(f"Extra dataset intents : {len(extra_dataset_intents)}")
    print()

    print("ZERO-EXAMPLE INTENTS")
    print("-" * 72)
    for intent in zero_example:
        print(intent)

    print()
    print("UNDERREPRESENTED INTENTS (<100)")
    print("-" * 72)
    for intent, count in underrepresented:
        print(f"{intent}: {count}")

    print()
    print("LARGEST INTENT CLASSES")
    print("-" * 72)

    for intent, count in intent_counts.most_common():
        print(f"{intent:35} {count}")

    print()
    print(f"[OK] Report saved to: {OUTPUT}")


if __name__ == "__main__":
    main()