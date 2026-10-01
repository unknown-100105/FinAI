from pathlib import Path
import json
import random

ROOT = Path(__file__).resolve().parents[1]

TRAIN = ROOT / "data" / "sft_v3_work" / "training_ready_v2" / "train.jsonl"
HARD = ROOT / "data" / "sft_v3_work" / "finai_v3_router_boost.jsonl"

OUT = ROOT / "data" / "sft_v3_work" / "finai_v3_router_pool_v2.jsonl"

ROUTER_SOURCES = {
    "FinAI-Intent-Seed",
    "FinAI-Contrastive-Synthetic",
}

rows = []

with TRAIN.open("r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        r = json.loads(line)

        if r.get("source_dataset") in ROUTER_SOURCES:
            rows.append(r)

print("EXISTING ROUTER:", len(rows))

hard_rows = []

with HARD.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            hard_rows.append(json.loads(line))

print("HARD NEGATIVES:", len(hard_rows))

# Avoid duplicate exact prompt+completion pairs.
seen = {
    (
        r.get("prompt", ""),
        r.get("completion", "")
    )
    for r in rows
}

added = 0

for r in hard_rows:
    key = (
        r.get("prompt", ""),
        r.get("completion", "")
    )

    if key not in seen:
        rows.append(r)
        seen.add(key)
        added += 1

random.Random(20260929).shuffle(rows)

OUT.parent.mkdir(parents=True, exist_ok=True)

with OUT.open("w", encoding="utf-8") as f:
    for r in rows:
        f.write(
            json.dumps(
                r,
                ensure_ascii=False
            ) + "\n"
        )

print("NEW HARD NEGATIVES ADDED:", added)
print("FINAL ROUTER POOL:", len(rows))
print("OUTPUT:", OUT)
