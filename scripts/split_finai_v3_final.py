from pathlib import Path
import json
import random
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "sft_v3_work" / "finai_v3_merged.jsonl"
OUT_DIR = ROOT / "data" / "sft_v3_work" / "final_split"

TRAIN = OUT_DIR / "train.jsonl"
VALIDATION = OUT_DIR / "validation.jsonl"
TEST = OUT_DIR / "test.jsonl"

MANIFEST = ROOT / "data" / "manifests" / "finai_v3_split_manifest.json"

SEED = 20260929


def is_finai_specific(row):
    return row.get("source_dataset") in {
        "FinAI-Intent-Seed",
        "FinAI-Contrastive-Synthetic",
    }


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(
                json.dumps(
                    row,
                    ensure_ascii=False
                ) + "\n"
            )


def main():
    print("=" * 72)
    print("FINAI-V3 FINAL DATASET SPLIT")
    print("=" * 72)

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Missing merged dataset: {INPUT}"
        )

    rows = []

    with INPUT.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if line.strip():
                rows.append(
                    json.loads(line)
                )

    base = [
        r for r in rows
        if not is_finai_specific(r)
    ]

    finai_specific = [
        r for r in rows
        if is_finai_specific(r)
    ]

    print()
    print("MASTER:", len(rows))
    print("BASE:", len(base))
    print(
        "FINAI-SPECIFIC:",
        len(finai_specific)
    )

    rng = random.Random(SEED)

    rng.shuffle(base)

    n = len(base)

    train_end = int(n * 0.90)
    validation_end = int(n * 0.95)

    base_train = base[:train_end]
    validation = base[
        train_end:validation_end
    ]
    test = base[
        validation_end:
    ]

    # All FinAI-specific router/contrastive data
    # stays in training.
    train = (
        finai_specific
        + base_train
    )

    rng.shuffle(train)

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    write_jsonl(
        TRAIN,
        train
    )

    write_jsonl(
        VALIDATION,
        validation
    )

    write_jsonl(
        TEST,
        test
    )

    source_train = Counter(
        r.get(
            "source_dataset",
            "unknown"
        )
        for r in train
    )

    source_validation = Counter(
        r.get(
            "source_dataset",
            "unknown"
        )
        for r in validation
    )

    source_test = Counter(
        r.get(
            "source_dataset",
            "unknown"
        )
        for r in test
    )

    manifest = {
        "dataset": "FinAI-V3 final split",
        "seed": SEED,
        "master_records": len(rows),
        "base_records": len(base),
        "finai_specific_records": len(
            finai_specific
        ),
        "train_records": len(train),
        "validation_records": len(validation),
        "test_records": len(test),
        "base_split": {
            "train": "90%",
            "validation": "5%",
            "test": "5%"
        },
        "finai_specific_policy": (
            "FinAI intent and contrastive augmentation "
            "records are training-only."
        ),
        "method": (
            "Deterministic seeded shuffle followed by "
            "90/5/5 positional split."
        ),
        "unseen_evaluation_policy": (
            "External unseen evaluation remains isolated."
        ),
        "sources_train": dict(source_train),
        "sources_validation": dict(
            source_validation
        ),
        "sources_test": dict(
            source_test
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

    print()
    print("=" * 72)
    print("FINAL SPLIT")
    print("=" * 72)

    print("TRAIN:", len(train))
    print(
        "VALIDATION:",
        len(validation)
    )
    print("TEST:", len(test))

    print()
    print("TOTAL:", (
        len(train)
        + len(validation)
        + len(test)
    ))

    print()
    print("TRAIN SOURCES:")
    for k, v in source_train.most_common():
        print(f"  {k}: {v}")

    print()
    print("VALIDATION SOURCES:")
    for k, v in source_validation.most_common():
        print(f"  {k}: {v}")

    print()
    print("TEST SOURCES:")
    for k, v in source_test.most_common():
        print(f"  {k}: {v}")

    print()
    print("[OK] Train:", TRAIN)
    print("[OK] Validation:", VALIDATION)
    print("[OK] Test:", TEST)
    print("[OK] Manifest:", MANIFEST)

    print("=" * 72)
    print("FINAI-V3 FINAL SPLIT COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
