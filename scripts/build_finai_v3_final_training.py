from pathlib import Path
import json
import random
import math

ROOT = Path(__file__).resolve().parents[1]

BASE_TRAIN = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "training_ready_v2"
    / "train.jsonl"
)

ROUTER_POOL = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_router_train_pool_v3.jsonl"
)

OUT_DIR = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "final_training_v3"
)

OUT_FILE = OUT_DIR / "train.jsonl"

SEED = 20260929
ROUTER_RATIO = 0.18

ROUTER_SOURCES = {
    "FinAI-Intent-Seed",
    "FinAI-Contrastive-Synthetic",
    "FinAI-Hard-Negative",
}


def wrap_qa(prompt):
    prompt = str(prompt).strip()

    if "<FINAI_QA>" in prompt:
        return prompt

    return (
        "<FINAI_QA>\n\n"
        + prompt
        + "\n\n"
        "</FINAI_QA>"
    )


def main():

    print("=" * 72)
    print("FINAI-V3 FINAL TRAINING DATASET - CORRECTED")
    print("=" * 72)

    if not BASE_TRAIN.exists():
        raise FileNotFoundError(BASE_TRAIN)

    if not ROUTER_POOL.exists():
        raise FileNotFoundError(ROUTER_POOL)

    # ------------------------------------------------------------
    # LOAD NORMAL FINANCIAL DATA
    # ------------------------------------------------------------

    normal = []

    with BASE_TRAIN.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if not line.strip():
                continue

            row = json.loads(line)

            # Remove all existing FinAI router rows from
            # the normal pool. They will come from ROUTER_POOL.
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

            if (
                source in ROUTER_SOURCES
                or "router" in task.lower()
            ):
                continue

            prompt = str(
                row.get(
                    "prompt",
                    ""
                )
            ).strip()

            completion = str(
                row.get(
                    "completion",
                    ""
                )
            ).strip()

            if not prompt or not completion:
                continue

            normal.append({
                "prompt": wrap_qa(prompt),
                "completion": completion,
                "source_dataset": source,
                "task_type": task or "financial_qa",
            })

    # ------------------------------------------------------------
    # LOAD ROUTER POOL
    # ------------------------------------------------------------

    router_pool = []

    with ROUTER_POOL.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if not line.strip():
                continue

            row = json.loads(line)

            prompt = str(
                row.get(
                    "prompt",
                    ""
                )
            ).strip()

            completion = str(
                row.get(
                    "completion",
                    ""
                )
            ).strip()

            if not prompt or not completion:
                continue

            # Explicitly normalize every router example.
            router_row = dict(row)

            router_row["task_type"] = "finai_router_v3"

            # Make sure the marker exists.
            if "<FINAI_ROUTER>" not in prompt:
                prompt = (
                    "<FINAI_ROUTER>\n\n"
                    + prompt
                    + "\n\n"
                    "</FINAI_ROUTER>"
                )

            router_row["prompt"] = prompt

            router_pool.append(router_row)

    print()
    print("NORMAL BASE:", len(normal))
    print("ROUTER POOL:", len(router_pool))

    if not normal:
        raise RuntimeError(
            "Normal training set is empty."
        )

    if not router_pool:
        raise RuntimeError(
            "Router pool is empty."
        )

    # ------------------------------------------------------------
    # CALCULATE ROUTER TARGET
    #
    # 18% router means:
    # router / (normal + router) = 0.18
    # ------------------------------------------------------------

    target_router = math.ceil(
        len(normal)
        * ROUTER_RATIO
        / (1.0 - ROUTER_RATIO)
    )

    print(
        "TARGET ROUTER:",
        target_router
    )

    # ------------------------------------------------------------
    # DETERMINISTIC OVERSAMPLING
    # ------------------------------------------------------------

    rng = random.Random(SEED)

    selected_router = []

    while len(selected_router) < target_router:

        remaining = (
            target_router
            - len(selected_router)
        )

        if remaining >= len(router_pool):

            batch = list(
                router_pool
            )

        else:

            batch = rng.sample(
                router_pool,
                remaining
            )

        selected_router.extend(
            batch
        )

    selected_router = selected_router[
        :target_router
    ]

    # ------------------------------------------------------------
    # FINAL DATASET
    # ------------------------------------------------------------

    final_rows = (
        normal
        + selected_router
    )

    rng.shuffle(
        final_rows
    )

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:

        for row in final_rows:

            f.write(
                json.dumps(
                    row,
                    ensure_ascii=False
                )
                + "\n"
            )

    # ------------------------------------------------------------
    # CORRECT STATISTICS
    # ------------------------------------------------------------

    router_count = sum(
        1
        for row in final_rows
        if row.get("task_type")
        == "finai_router_v3"
    )

    normal_count = (
        len(final_rows)
        - router_count
    )

    router_percent = (
        router_count
        / len(final_rows)
        * 100
    )

    # ------------------------------------------------------------
    # CHECK MARKERS
    # ------------------------------------------------------------

    router_markers = sum(
        1
        for row in final_rows
        if (
            row.get("task_type")
            == "finai_router_v3"
            and "<FINAI_ROUTER>" in row.get(
                "prompt",
                ""
            )
        )
    )

    qa_markers = sum(
        1
        for row in final_rows
        if (
            row.get("task_type")
            != "finai_router_v3"
            and "<FINAI_QA>" in row.get(
                "prompt",
                ""
            )
        )
    )

    print()
    print("=" * 72)
    print("FINAL TRAINING DATASET")
    print("=" * 72)

    print(
        "NORMAL:",
        normal_count
    )

    print(
        "ROUTER:",
        router_count
    )

    print(
        "TOTAL:",
        len(final_rows)
    )

    print(
        "ROUTER %:",
        round(
            router_percent,
            2
        )
    )

    print()
    print(
        "ROUTER MARKERS:",
        router_markers
    )

    print(
        "QA MARKERS:",
        qa_markers
    )

    print()
    print(
        "[OK] Dataset:",
        OUT_FILE
    )

    print("=" * 72)
    print(
        "FINAI-V3 FINAL TRAINING DATASET COMPLETE"
    )
    print("=" * 72)


if __name__ == "__main__":
    main()
