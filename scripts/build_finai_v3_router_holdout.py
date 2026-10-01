from pathlib import Path
import json
import random
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_router_pool_v2.jsonl"
)

TRAIN_POOL = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_router_train_pool_v3.jsonl"
)

ROUTER_EVAL = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_router_eval_v3.jsonl"
)

SEED = 20260930

# We want 20 held-out examples per intent:
# 10 validation + 10 test.
PER_INTENT_TOTAL = 20


def main():

    print("=" * 72)
    print("FINAI-V3 ROUTER HELD-OUT BENCHMARK")
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

    print("INPUT ROUTER RECORDS:", len(rows))

    groups = defaultdict(list)

    for row in rows:

        intent = str(
            row.get(
                "intent",
                ""
            )
        ).strip()

        language = str(
            row.get(
                "language",
                "en"
            )
        ).strip()

        if intent:
            groups[
                (intent, language)
            ].append(row)

    rng = random.Random(SEED)

    for key in groups:
        rng.shuffle(groups[key])

    heldout = []
    used_keys = set()

    # --------------------------------------------------------------
    # Try to select 4 examples per intent-language combination.
    # There are 50 intents x 5 languages = 250 groups.
    # 250 x 4 = 1,000 examples.
    # --------------------------------------------------------------

    for (intent, language), group in sorted(
        groups.items()
    ):

        take = min(
            4,
            len(group)
        )

        for row in group[:take]:

            # Use prompt+completion as the identity.
            key = (
                row.get("prompt", ""),
                row.get("completion", "")
            )

            if key in used_keys:
                continue

            used_keys.add(key)
            heldout.append(row)

    # --------------------------------------------------------------
    # If some groups had insufficient data, fill deterministically
    # from remaining examples while keeping intent coverage.
    # --------------------------------------------------------------

    target = min(
        1000,
        len(rows) // 2
    )

    if len(heldout) < target:

        remaining = [
            row
            for row in rows
            if (
                row.get("prompt", ""),
                row.get("completion", "")
            ) not in used_keys
        ]

        rng.shuffle(remaining)

        for row in remaining:

            key = (
                row.get("prompt", ""),
                row.get("completion", "")
            )

            if key in used_keys:
                continue

            heldout.append(row)
            used_keys.add(key)

            if len(heldout) >= target:
                break

    # --------------------------------------------------------------
    # Split held-out benchmark.
    # --------------------------------------------------------------

    rng.shuffle(heldout)

    validation = heldout[: len(heldout) // 2]
    test = heldout[len(heldout) // 2:]

    # --------------------------------------------------------------
    # Remove held-out records from training pool.
    # --------------------------------------------------------------

    training_pool = []

    for row in rows:

        key = (
            row.get("prompt", ""),
            row.get("completion", "")
        )

        if key not in used_keys:
            training_pool.append(row)

    # --------------------------------------------------------------
    # Write training router pool.
    # --------------------------------------------------------------

    TRAIN_POOL.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with TRAIN_POOL.open(
        "w",
        encoding="utf-8"
    ) as f:

        for row in training_pool:

            f.write(
                json.dumps(
                    row,
                    ensure_ascii=False
                ) + "\n"
            )

    # --------------------------------------------------------------
    # Write held-out benchmark with split field.
    # --------------------------------------------------------------

    with ROUTER_EVAL.open(
        "w",
        encoding="utf-8"
    ) as f:

        for row in validation:

            out = dict(row)
            out["eval_split"] = "validation"

            f.write(
                json.dumps(
                    out,
                    ensure_ascii=False
                ) + "\n"
            )

        for row in test:

            out = dict(row)
            out["eval_split"] = "test"

            f.write(
                json.dumps(
                    out,
                    ensure_ascii=False
                ) + "\n"
            )

    # --------------------------------------------------------------
    # Statistics.
    # --------------------------------------------------------------

    train_intents = Counter(
        r.get("intent")
        for r in training_pool
    )

    eval_intents = Counter(
        r.get("intent")
        for r in heldout
    )

    eval_languages = Counter(
        r.get("language")
        for r in heldout
    )

    print()
    print("TRAINING ROUTER POOL:", len(training_pool))
    print("HELD-OUT TOTAL:", len(heldout))
    print("HELD-OUT VALIDATION:", len(validation))
    print("HELD-OUT TEST:", len(test))

    print()
    print("HELD-OUT INTENTS:", len(eval_intents))

    print()
    print("HELD-OUT LANGUAGES:")

    for language, count in sorted(
        eval_languages.items()
    ):
        print(
            f"  {language}: {count}"
        )

    print()
    print("[OK] Router training pool:")
    print(TRAIN_POOL)

    print()
    print("[OK] Router held-out benchmark:")
    print(ROUTER_EVAL)

    print()
    print("=" * 72)
    print("ROUTER HELD-OUT BENCHMARK COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
