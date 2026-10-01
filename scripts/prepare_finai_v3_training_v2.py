from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = ROOT / "data" / "sft_v3_work" / "final_split_v2"
OUTPUT_DIR = ROOT / "data" / "sft_v3_work" / "training_ready_v2"

FILES = [
    "train.jsonl",
    "validation.jsonl",
    "test.jsonl",
]

ROUTER_SOURCES = {
    "FinAI-Intent-Seed",
    "FinAI-Contrastive-Synthetic",
}


def router_prompt(user):
    return (
        "You are FinAI, a financial-domain assistant.\n\n"
        "For FinAI routing requests, identify the user's intent "
        "and return the response using exactly this format:\n"
        "INTENT: <intent>\n"
        "RISK_LEVEL: <low|medium|high>\n"
        "REQUIRES_TOOL: <true|false>\n"
        "TOOL: <tool name or NONE>\n"
        "RESPONSE: <helpful answer>\n\n"
        "Do not add extra fields.\n\n"
        "USER:\n"
        + str(user).strip()
    )


def normal_prompt(user):
    return (
        "You are FinAI, a financial-domain assistant.\n\n"
        "USER:\n"
        + str(user).strip()
    )


def router_completion(row):
    intent = str(
        row.get("intent", "")
    ).strip()

    risk = str(
        row.get("risk_level", "medium")
    ).strip().lower()

    requires_tool = bool(
        row.get("requires_tool", False)
    )

    tool = str(
        row.get("tool_name", "")
    ).strip()

    if not tool:
        tool = "NONE"

    answer = str(
        row.get("assistant", "")
    ).strip()

    return (
        f"INTENT: {intent}\n"
        f"RISK_LEVEL: {risk}\n"
        f"REQUIRES_TOOL: {str(requires_tool).lower()}\n"
        f"TOOL: {tool}\n"
        f"RESPONSE: {answer}"
    )


def process_file(filename):

    source_path = INPUT_DIR / filename
    output_path = OUTPUT_DIR / filename

    if not source_path.exists():
        raise FileNotFoundError(source_path)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    total = 0
    router = 0
    normal = 0

    with source_path.open(
        "r",
        encoding="utf-8"
    ) as src, output_path.open(
        "w",
        encoding="utf-8"
    ) as dst:

        for line in src:

            if not line.strip():
                continue

            row = json.loads(line)

            user = str(
                row.get("user", "")
            ).strip()

            assistant = str(
                row.get("assistant", "")
            ).strip()

            if not user or not assistant:
                continue

            source = str(
                row.get(
                    "source_dataset",
                    ""
                )
            )

            if source in ROUTER_SOURCES:

                prompt = router_prompt(user)
                completion = router_completion(row)

                router += 1

            else:

                prompt = normal_prompt(user)
                completion = assistant

                normal += 1

            output = {
                "prompt": prompt,
                "completion": completion,
                "source_dataset": source,
                "task_type": row.get(
                    "task_type",
                    ""
                ),
            }

            for field in (
                "intent",
                "language",
                "risk_level",
                "requires_tool",
                "tool_name",
                "contrastive_pair",
            ):

                if field in row:
                    output[field] = row[field]

            dst.write(
                json.dumps(
                    output,
                    ensure_ascii=False
                ) + "\n"
            )

            total += 1

    print()
    print("=" * 72)
    print(filename)
    print("=" * 72)
    print("TOTAL:", total)
    print("ROUTER:", router)
    print("NORMAL:", normal)
    print("OUTPUT:", output_path)


def main():

    print("=" * 72)
    print("FINAI-V3 TRAINING-READY DATASET")
    print("=" * 72)

    for filename in FILES:
        process_file(filename)

    print()
    print("=" * 72)
    print("FINAI-V3 TRAINING-READY COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
