from pathlib import Path
import json
import hashlib
import re
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "sft_final_old" / "train.jsonl"
OUTPUT = ROOT / "data" / "sft_v3_work" / "finai_v3_intent_seed.jsonl"
MANIFEST = ROOT / "data" / "manifests" / "finai_v3_intent_seed_manifest.json"

LANGUAGES = {"en", "ta", "te", "kn", "ml"}
PER_LANGUAGE = 25


def clean(value):
    if value is None:
        return ""

    text = str(value)
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_user(prompt):
    text = str(prompt or "")

    match = re.search(
        r"###\s*User\s*:\s*(.*?)\s*###\s*Assistant\s*:",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return clean(match.group(1))

    return clean(text)


def make_key(record):
    raw = (
        record["intent"]
        + "\n"
        + record["language"]
        + "\n"
        + record["user"]
        + "\n"
        + record["assistant"]
    )

    return hashlib.sha256(
        raw.lower().encode("utf-8")
    ).hexdigest()


def valid(record):
    if not record["intent"]:
        return False

    if record["language"] not in LANGUAGES:
        return False

    if len(record["user"]) < 8:
        return False

    if len(record["assistant"]) < 5:
        return False

    if len(record["user"]) > 12000:
        return False

    if len(record["assistant"]) > 12000:
        return False

    return True


def main():
    if not INPUT.exists():
        raise FileNotFoundError(
            f"Missing input: {INPUT}"
        )

    groups = defaultdict(list)

    total = 0
    accepted = 0
    skipped = Counter()

    with INPUT.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            if not line.strip():
                continue

            total += 1

            try:
                source = json.loads(line)
            except Exception:
                skipped["invalid_json"] += 1
                continue

            intent = clean(
                source.get("intent", "")
            )

            language = clean(
                source.get("language", "")
            ).lower()

            prompt = source.get(
                "prompt",
                source.get("question", "")
            )

            completion = source.get(
                "completion",
                source.get(
                    "response",
                    source.get("assistant", "")
                )
            )

            user = extract_user(prompt)
            assistant = clean(completion)

            record = {
                "source_dataset": "FinAI-Intent-Seed",
                "task_type": "finai_router",
                "intent": intent,
                "language": language,
                "user": user,
                "assistant": assistant,
                "risk_level": clean(
                    source.get("risk_level", "")
                ),
                "requires_tool": bool(
                    source.get(
                        "requires_tool",
                        False
                    )
                ),
                "tool_name": clean(
                    source.get(
                        "tool_name",
                        ""
                    )
                ),
            }

            if not intent:
                skipped["missing_intent"] += 1
                continue

            if language not in LANGUAGES:
                skipped["unsupported_language"] += 1
                continue

            if not valid(record):
                skipped["quality_filter"] += 1
                continue

            groups[
                (intent, language)
            ].append(record)

            accepted += 1

    print("=" * 72)
    print("FINAI-V3 CLEAN INTENT SELECTION")
    print("=" * 72)

    print()
    print("INPUT RECORDS:", total)
    print("ACCEPTED BEFORE SAMPLING:", accepted)

    print()
    print("SKIPPED:")
    for key, value in skipped.most_common():
        print(
            f"  {key}: {value}"
        )

    selected = []

    for key, records in sorted(
        groups.items()
    ):

        records.sort(
            key=make_key
        )

        selected.extend(
            records[:PER_LANGUAGE]
        )

    seen = set()
    unique = []

    for record in selected:

        key = make_key(record)

        if key in seen:
            continue

        seen.add(key)
        unique.append(record)

    unique.sort(
        key=make_key
    )

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
                + "\n"
            )

    by_language = Counter(
        r["language"]
        for r in unique
    )

    by_intent = Counter(
        r["intent"]
        for r in unique
    )

    manifest = {
        "dataset": "FinAI-V3 intent seed",
        "source": str(INPUT),
        "input_records": total,
        "accepted_before_sampling": accepted,
        "final_records": len(unique),
        "per_language_target": PER_LANGUAGE,
        "languages": sorted(LANGUAGES),
        "intent_count": len(by_intent),
        "language_distribution": dict(by_language),
        "intent_distribution": dict(by_intent),
        "skipped": dict(skipped),
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
    print("UNIQUE INTENTS:", len(by_intent))

    print()
    print("BY LANGUAGE:")
    for language, count in sorted(
        by_language.items()
    ):
        print(
            f"  {language}: {count}"
        )

    print()
    print("FINAL RECORDS:", len(unique))

    print()
    print("[OK] Dataset:")
    print(OUTPUT)

    print()
    print("[OK] Manifest:")
    print(MANIFEST)

    print("=" * 72)
    print("FINAI-V3 INTENT SEED COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
