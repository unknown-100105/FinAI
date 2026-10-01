import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SOURCE_DIR = ROOT / "data" / "processed_large"
OUTPUT_DIR = ROOT / "data" / "sft"

FILES = {
    "train.jsonl": "train.jsonl",
    "validation.jsonl": "validation.jsonl",
    "test.jsonl": "test.jsonl",
}


def convert_record(record):
    prompt = (
        "### User:\n"
        f"{record['text']}\n\n"
        "### Assistant:\n"
    )

    completion = record["response"]

    return {
        "prompt": prompt,
        "completion": completion,
        "language": record["language"],
        "intent": record["intent"],
        "risk_level": record["risk_level"],
        "requires_tool": record["requires_tool"],
        "tool_name": record["tool_name"],
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for input_name, output_name in FILES.items():

        source = SOURCE_DIR / input_name
        output = OUTPUT_DIR / output_name

        count = 0

        with source.open("r", encoding="utf-8") as src, \
             output.open("w", encoding="utf-8") as dst:

            for line in src:
                line = line.strip()

                if not line:
                    continue

                record = json.loads(line)
                converted = convert_record(record)

                dst.write(
                    json.dumps(
                        converted,
                        ensure_ascii=False
                    ) + "\n"
                )

                count += 1

        print(f"{input_name}: {count} examples")

    print("=" * 60)
    print("SFT DATASET PREPARATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()