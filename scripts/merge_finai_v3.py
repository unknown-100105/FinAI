from pathlib import Path
import json
import hashlib
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

INPUTS = [
    ROOT / "data" / "sft_v3_work" / "finai_v3_base.jsonl",
    ROOT / "data" / "sft_v3_work" / "finai_v3_intent_seed.jsonl",
    ROOT / "data" / "sft_v3_work" / "finai_v3_contrastive.jsonl",
]

OUT = ROOT / "data" / "sft_v3_work" / "finai_v3_merged.jsonl"
MANIFEST = ROOT / "data" / "manifests" / "finai_v3_merged_manifest.json"


def normalize(x):
    return " ".join(str(x or "").split()).strip().lower()


def fingerprint(row):
    text = (
        normalize(row.get("user"))
        + "\n"
        + normalize(row.get("assistant"))
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    print("=" * 72)
    print("FINAI-V3 FINAL DATASET MERGE")
    print("=" * 72)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    seen = set()
    records = []

    source_counts = Counter()
    task_counts = Counter()
    language_counts = Counter()
    duplicates = 0
    invalid = 0

    for path in INPUTS:
        print()
        print("READING:", path)

        if not path.exists():
            raise FileNotFoundError(path)

        local = 0

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                row = json.loads(line)

                user = str(row.get("user", "")).strip()
                assistant = str(row.get("assistant", "")).strip()

                if not user or not assistant:
                    invalid += 1
                    continue

                fp = fingerprint(row)

                if fp in seen:
                    duplicates += 1
                    continue

                seen.add(fp)
                records.append(row)

                source_counts[row.get("source_dataset", "unknown")] += 1
                task_counts[row.get("task_type", "unknown")] += 1
                language_counts[row.get("language", "unknown")] += 1

                local += 1

        print("  ACCEPTED:", local)

    with OUT.open("w", encoding="utf-8") as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "dataset": "FinAI-V3 merged dataset",
        "records": len(records),
        "input_records_expected": 134515 + 6250 + 436,
        "duplicates_removed": duplicates,
        "invalid_records_removed": invalid,
        "records_by_source": dict(source_counts),
        "records_by_task": dict(task_counts),
        "records_by_language": dict(language_counts),
        "deduplication": "SHA-256 of normalized user + assistant",
        "inputs": [str(p) for p in INPUTS],
        "output": str(OUT),
    }

    MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("FINAL MERGED DATASET")
    print("=" * 72)

    print("RAW INPUT:", 134515 + 6250 + 436)
    print("FINAL RECORDS:", len(records))
    print("DUPLICATES REMOVED:", duplicates)
    print("INVALID REMOVED:", invalid)

    print()
    print("BY SOURCE:")
    for k, v in source_counts.most_common():
        print(f"  {k}: {v}")

    print()
    print("BY TASK:")
    for k, v in task_counts.most_common():
        print(f"  {k}: {v}")

    print()
    print("BY LANGUAGE:")
    for k, v in language_counts.most_common():
        print(f"  {k}: {v}")

    print()
    print("[OK] Dataset:", OUT)
    print("[OK] Manifest:", MANIFEST)
    print("=" * 72)
    print("FINAI-V3 MERGE COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
