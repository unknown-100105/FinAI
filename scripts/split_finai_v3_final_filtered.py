from pathlib import Path
import json
import random
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_domain_master_v2.jsonl"
)

OUT_DIR = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "final_split_v2"
)

TRAIN = OUT_DIR / "train.jsonl"
VALIDATION = OUT_DIR / "validation.jsonl"
TEST = OUT_DIR / "test.jsonl"

MANIFEST = (
    ROOT
    / "data"
    / "manifests"
    / "finai_v3_final_split_v2_manifest.json"
)

SEED = 20260929

FINAI_SPECIFIC = {
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
    print("FINAI-V3 FINAL FILTERED DATASET SPLIT")
    print("=" * 72)

    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

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

    finai_specific = []
    base = []

    for row in rows:

        if row.get("source_dataset") in FINAI_SPECIFIC:
            finai_specific.append(row)
        else:
            base.append(row)

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

    train_end = int(
        n * 0.90
    )

    validation_end = int(
        n * 0.95
    )

    base_train = base[
        :train_end
    ]

    validation = base[
        train_end:validation_end
    ]

    test = base[
        validation_end:
    ]

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

    train_sources = Counter(
        r.get(
            "source_dataset",
            "unknown"
        )
        for r in train
    )

    validation_sources = Counter(
        r.get(
            "source_dataset",
            "unknown"
        )
        for r in validation
    )

    test_sources = Counter(
        r.get(
            "source_dataset",
            "unknown"
        )
        for r in test
    )

    manifest = {
        "dataset": "FinAI-V3 final filtered split",
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
            "test": "5%",
        },
        "finai_specific_policy": (
            "FinAI Intent Seed and FinAI Contrastive "
            "Synthetic records are training-only."
        ),
        "input": str(INPUT),
        "train": str(TRAIN),
        "validation": str(VALIDATION),
        "test": str(TEST),
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

    print(
        "TOTAL:",
        len(train)
        + len(validation)
        + len(test)
    )

    print()
    print("TRAIN SOURCES:")
    for k, v in train_sources.most_common():
        print(f"  {k}: {v}")

    print()
    print("VALIDATION SOURCES:")
    for k, v in validation_sources.most_common():
        print(f"  {k}: {v}")

    print()
    print("TEST SOURCES:")
    for k, v in test_sources.most_common():
        print(f"  {k}: {v}")

    print()
    print("[OK] Train:", TRAIN)
    print("[OK] Validation:", VALIDATION)
    print("[OK] Test:", TEST)
    print("[OK] Manifest:", MANIFEST)

    print()
    print("=" * 72)
    print("FINAI-V3 FINAL FILTERED SPLIT COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
