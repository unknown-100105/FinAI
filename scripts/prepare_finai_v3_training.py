from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = ROOT / "data" / "sft_v3_work" / "final_split"
OUTPUT_DIR = ROOT / "data" / "sft_v3_work" / "training_ready"

FILES = ["train.jsonl", "validation.jsonl", "test.jsonl"]

ROUTER_SOURCES = {
    "FinAI-Intent-Seed",
    "FinAI-Contrastive-Synthetic",
}


def router_prompt(user):
    return (
        "You are FinAI, a financial-domain assistant.\n"
        "For FinAI routing requests, identify the user's intent and "
        "return the response using exactly this format:\n\n"
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
    intent = str(row.get("intent", "")).strip()
    risk = str(row.get("risk_level", "medium")).strip().lower()

    requires_tool = row.get("requires_tool", False)
    tool = str(row.get("tool_name", "")).strip()

    if not tool:
        tool = "NONE"

    answer = str(row.get("assistant", "")).strip()

    return (
        f"INTENT: {intent}\n"
        f"RISK_LEVEL: {risk}\n"
        f"REQUIRES_TOOL: {str(bool(requires_tool)).lower()}\n"
        f"TOOL: {tool}\n"
        f"RESPONSE: {answer}"
    )


def normal_completion(row):
    return str(row.get("assistant", "")).strip()


def process_file(filename):

    input_path = INPUT_DIR / filename
    output_path = OUTPUT_DIR / filename

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    total = 0
    router = 0
    normal = 0
    invalid = 0

    with input_path.open(
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
                invalid += 1
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
                completion = normal_completion(row)
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
    print("FILE:", filename)
    print("TOTAL:", total)
    print("ROUTER:", router)
    print("NORMAL:", normal)
    print("INVALID:", invalid)
    print("OUTPUT:", output_path)
    print("=" * 72)


def main():

    print("=" * 72)
    print("FINAI-V3 TRAINING DATA PREPARATION")
    print("=" * 72)

    for filename in FILES:
        process_file(filename)

    print()
    print("FINAI-V3 TRAINING DATA PREPARATION COMPLETE")


if __name__ == "__main__":
    main()
