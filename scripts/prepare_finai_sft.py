import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIR = ROOT / "data" / "processed_large"
OUTPUT_DIR = ROOT / "data" / "sft_v2"

FILES = [
    "train.jsonl",
    "validation.jsonl",
    "test.jsonl",
]


def convert(record):
    assistant_text = (
        f"INTENT: {record['intent']}\n"
        f"RISK_LEVEL: {record['risk_level']}\n"
        f"REQUIRES_TOOL: {str(record['requires_tool']).lower()}\n"
        f"TOOL: {record['tool_name'] or 'none'}\n"
        f"RESPONSE: {record['response']}"
    )

    return {
        "prompt": [
            {
                "role": "user",
                "content": record["text"],
            }
        ],
        "completion": [
            {
                "role": "assistant",
                "content": assistant_text,
            }
        ],
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename in FILES:
        source = SOURCE_DIR / filename
        output = OUTPUT_DIR / filename

        count = 0

        with source.open("r", encoding="utf-8") as src, \
             output.open("w", encoding="utf-8") as dst:

            for line in src:
                line = line.strip()

                if not line:
                    continue

                record = json.loads(line)
                converted = convert(record)

                dst.write(
                    json.dumps(
                        converted,
                        ensure_ascii=False
                    ) + "\n"
                )

                count += 1

        print(f"{filename}: {count} examples")

    print("=" * 60)
    print("FINAI SFT V2 PREPARATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()