from pathlib import Path
import json
import hashlib
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "sft_v3_work" / "finai_v3_candidates.jsonl"
WORK = ROOT / "data" / "sft_v3_work"

OUTPUT = WORK / "finai_v3_base.jsonl"
MANIFEST = ROOT / "data" / "manifests" / "finai_v3_base_manifest.json"


TARGETS = {
    "financial_instruction": 65000,
    "qa": 20000,
    "qa_with_context": 15000,
    "financial_reasoning": 12000,
    "financial_table_reasoning": 10000,
    "numeric_reasoning": 8000,
    "qa_conversation": 5000,
    "risk_analysis": 1000,
    "sentiment_analysis": 2000,
    "topic_classification": 2000,
    "ner_sentiment_analysis": 500,
}


def stable_score(record):
    text = (
        record.get("user", "")
        + chr(10)
        + record.get("assistant", "")
    ).lower()

    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def valid_record(record):
    user = str(record.get("user", ""))
    assistant = str(record.get("assistant", ""))

    if len(user) < 10:
        return False

    if len(assistant) < 1:
        return False

    # Avoid very expensive examples for the 8 GB GPU.
    if len(user) > 12000:
        return False

    if len(assistant) > 12000:
        return False

    return True


def keep_small_n(records, n):
    if len(records) <= n:
        return records

    records.sort(key=stable_score)
    return records[:n]


def main():
    print("=" * 72)
    print("FINAI-V3 FINAL BASE DATASET SELECTOR")
    print("=" * 72)

    groups = {}

    with INPUT.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            if not valid_record(record):
                continue

            task = record.get(
                "task_type",
                "financial_instruction"
            )

            groups.setdefault(task, []).append(record)

    print("\nAVAILABLE RECORDS:")

    for task, records in sorted(
        groups.items(),
        key=lambda x: len(x[1]),
        reverse=True
    ):
        print(f"  {task}: {len(records)}")

    selected = []

    print("\nSELECTION:")

    for task, target in TARGETS.items():
        available = groups.get(task, [])

        chosen = keep_small_n(
            available,
            target
        )

        selected.extend(chosen)

        print(
            f"  {task}: "
            f"{len(chosen)} / {target}"
        )

    # Some datasets may have fewer examples than the target.
    # Do not fabricate data here.
    selected.sort(key=stable_score)

    # Final exact deduplication.
    seen = set()
    unique = []

    for record in selected:
        key = hashlib.sha256(
            (
                record.get("user", "").lower()
                + chr(10)
                + record.get("assistant", "").lower()
            ).encode("utf-8")
        ).hexdigest()

        if key in seen:
            continue

        seen.add(key)
        unique.append(record)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT.open(
        "w",
        encoding="utf-8"
    ) as file:
        for record in unique:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + chr(10)
            )

    by_source = Counter(
        record.get(
            "source_dataset",
            "unknown"
        )
        for record in unique
    )

    by_task = Counter(
        record.get(
            "task_type",
            "unknown"
        )
        for record in unique
    )

    manifest = {
        "dataset": "FinAI-V3 base SFT dataset",
        "input_records": sum(
            len(v) for v in groups.values()
        ),
        "selected_before_final_dedup": len(selected),
        "final_records": len(unique),
        "duplicates_removed_in_final_pass": (
            len(selected) - len(unique)
        ),
        "target_by_task": TARGETS,
        "records_by_source": dict(by_source),
        "records_by_task": dict(by_task),
        "max_user_chars": 12000,
        "max_assistant_chars": 12000,
        "selection_method": (
            "Deterministic SHA-256 sampling within each task"
        ),
    }

    MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    MANIFEST.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("\nFINAL DATASET")
    print("-" * 72)
    print("Records:", len(unique))

    print("\nBY SOURCE:")
    for name, count in by_source.most_common():
        print(f"  {name}: {count}")

    print("\nBY TASK:")
    for name, count in by_task.most_common():
        print(f"  {name}: {count}")

    print("\n[OK] Dataset:")
    print(OUTPUT)

    print("[OK] Manifest:")
    print(MANIFEST)

    print("=" * 72)
    print("FINAI-V3 BASE DATASET SELECTION COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
