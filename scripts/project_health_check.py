import json
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ============================================================
# HELPERS
# ============================================================

def check_file(path, label):
    exists = path.exists()

    print(
        f"[{'OK' if exists else 'MISSING'}] {label}: {path}"
    )

    return exists


def count_jsonl(path):
    if not path.exists():
        return 0

    count = 0

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                count += 1

    return count


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("FINAI PROJECT HEALTH CHECK")
    print("=" * 72)

    problems = []

    # --------------------------------------------------------
    # Core package
    # --------------------------------------------------------

    print("\nCORE PACKAGE")

    core_files = [
        ROOT / "finai" / "__init__.py",
        ROOT / "finai" / "model.py",
        ROOT / "finai" / "pipeline.py",
        ROOT / "finai" / "rag.py",
        ROOT / "finai" / "router.py",
        ROOT / "finai" / "safety.py",
        ROOT / "finai" / "tools.py",
        ROOT / "finai" / "chatbot.py",
    ]

    for path in core_files:
        if not check_file(path, path.name):
            problems.append(str(path))

    # --------------------------------------------------------
    # SFT datasets
    # --------------------------------------------------------

    print("\nSFT DATASETS")

    expected_splits = {
        "train": 16000,
        "validation": 2000,
        "test": 2000,
    }

    for folder_name in ["sft_v2", "sft_final"]:

        folder = ROOT / "data" / folder_name

        print(f"\n{folder_name}")

        for split, expected in expected_splits.items():

            path = folder / f"{split}.jsonl"

            if not path.exists():

                problems.append(str(path))
                print(
                    f"[MISSING] {split}: {path}"
                )
                continue

            count = count_jsonl(path)

            status = "OK" if count == expected else "CHECK"

            print(
                f"[{status}] {split}: {count} "
                f"(expected {expected})"
            )

            if count != expected:
                problems.append(
                    f"{path}: {count} != {expected}"
                )

    # --------------------------------------------------------
    # Domain data
    # --------------------------------------------------------

    print("\nDOMAIN DATA")

    domain_files = [
        ROOT / "data" / "domain" / "finllm_india_clean.jsonl",
        ROOT / "data" / "domain" / "indian_financial_news_clean.jsonl",
        ROOT / "data" / "domain_train" / "domain_train_20k.jsonl",
    ]

    for path in domain_files:

        if not check_file(path, path.name):
            problems.append(str(path))

    # --------------------------------------------------------
    # RAG
    # --------------------------------------------------------

    print("\nRAG")

    rag_db = ROOT / "data" / "rag" / "finai_rag.db"

    if not check_file(rag_db, "RAG database"):
        problems.append(str(rag_db))

    # --------------------------------------------------------
    # Layer 1 adapter
    # --------------------------------------------------------

    print("\nLAYER 1 ADAPTER")

    layer1 = ROOT / "models" / "finai-domain-lora"

    layer1_files = [
        layer1 / "adapter_config.json",
        layer1 / "adapter_model.safetensors",
    ]

    for path in layer1_files:

        if not check_file(path, path.name):
            problems.append(str(path))

    # --------------------------------------------------------
    # Layer 2 smoke adapter
    # --------------------------------------------------------

    print("\nLAYER 2 SMOKE TEST")

    layer2_smoke = (
        ROOT
        / "models"
        / "finai-v2-lora-smoke"
    )

    layer2_files = [
        layer2_smoke / "adapter_config.json",
        layer2_smoke / "adapter_model.safetensors",
    ]

    for path in layer2_files:

        if not check_file(path, path.name):
            problems.append(str(path))

    # --------------------------------------------------------
    # Layer 2 full adapter
    # --------------------------------------------------------

    print("\nLAYER 2 FULL ADAPTER")

    layer2_full = (
        ROOT
        / "models"
        / "finai-v2-lora"
    )

    if layer2_full.exists():

        print(
            "[PRESENT] Full Layer-2 adapter already exists."
        )

    else:

        print(
            "[NOT YET CREATED] This is expected before full training."
        )

    # --------------------------------------------------------
    # Router/tool integrity
    # --------------------------------------------------------

    print("\nROUTER / TOOL INTEGRITY")

    try:

        from finai.router import (
            INTENT_TO_TOOL,
            NO_TOOL_INTENTS,
        )

        from finai.tools import TOOLS

        print(
            "Router intents:",
            len(INTENT_TO_TOOL)
        )

        print(
            "No-tool intents:",
            len(NO_TOOL_INTENTS)
        )

        print(
            "Registered tools:",
            len(TOOLS)
        )

        missing_tools = [
            tool
            for tool in INTENT_TO_TOOL.values()
            if tool not in TOOLS
        ]

        if missing_tools:

            print(
                "[CHECK] Missing registered tools:"
            )

            for tool in sorted(set(missing_tools)):
                print(" ", tool)

            problems.append(
                "Missing registered tools"
            )

        else:

            print(
                "[OK] All router tools are registered."
            )

    except Exception as error:

        print(
            "[ERROR] Router/tool import failed:"
        )

        print(
            type(error).__name__,
            str(error)
        )

        problems.append(
            "Router/tool import failed"
        )

    # --------------------------------------------------------
    # Model training script
    # --------------------------------------------------------

    print("\nTRAINING SCRIPT")

    training_script = (
        ROOT
        / "scripts"
        / "train_finai_v2.py"
    )

    if training_script.exists():

        text = training_script.read_text(
            encoding="utf-8"
        )

        if "SMOKE_TEST = False" in text:

            print(
                "[OK] Full-training mode is configured."
            )

        elif "SMOKE_TEST = True" in text:

            print(
                "[INFO] Smoke-test mode is still enabled."
            )

        else:

            print(
                "[CHECK] Could not determine SMOKE_TEST setting."
            )

    else:

        problems.append(
            str(training_script)
        )

        print(
            "[MISSING] train_finai_v2.py"
        )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("\n" + "=" * 72)

    if not problems:

        print("FINAI PROJECT HEALTH: OK")

    else:

        print(
            "FINAI PROJECT HEALTH: NEEDS ATTENTION"
        )

        print("\nItems to review:")

        for problem in problems:
            print("-", problem)

    print("=" * 72)


if __name__ == "__main__":
    main()