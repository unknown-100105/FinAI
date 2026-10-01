from pathlib import Path
import json
import re
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
)
from peft import PeftModel


ROOT = Path(__file__).resolve().parents[1]

MODEL_NAME = "sarvamai/sarvam-1"

ADAPTER_DIR = (
    ROOT
    / "models"
    / "finai-v3-final-smoke"
)

EVAL_FILE = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_router_eval_v3.jsonl"
)

RESULT_FILE = (
    ROOT
    / "evaluation"
    / "finai_v3_smoke_router_results.json"
)

MAX_NEW_TOKENS = 80


def extract_expected(completion):
    m = re.search(
        r"INTENT:\s*([A-Z0-9_]+)",
        str(completion),
        re.IGNORECASE,
    )
    return (
        m.group(1).upper()
        if m
        else None
    )


def extract_predicted(text):
    m = re.search(
        r"INTENT:\s*([A-Z0-9_]+)",
        str(text),
        re.IGNORECASE,
    )

    if not m:
        return None

    return m.group(1).upper()


def load_records():
    rows = []

    with EVAL_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if not line.strip():
                continue

            row = json.loads(line)

            if row.get("eval_split") != "test":
                continue

            expected = extract_expected(
                row.get("completion", "")
            )

            prompt = str(
                row.get("prompt", "")
            ).strip()

            if not prompt or not expected:
                continue

            rows.append({
                "prompt": prompt,
                "expected": expected,
                "language": row.get(
                    "language",
                    "unknown"
                ),
            })

    return rows


def main():

    print("=" * 72)
    print("FINAI-V3 SMOKE ROUTER BENCHMARK")
    print("=" * 72)

    if not ADAPTER_DIR.exists():
        raise FileNotFoundError(
            f"Adapter not found: {ADAPTER_DIR}"
        )

    if not EVAL_FILE.exists():
        raise FileNotFoundError(
            f"Evaluation file not found: {EVAL_FILE}"
        )

    rows = load_records()

    print()
    print("TEST RECORDS:", len(rows))

    print()
    print("Loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        trust_remote_code=True,
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("Tokenizer loaded.")

    print()
    print("Loading base model in 4-bit...")

    quant_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    base_model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=quant_config,
        device_map="auto",
        torch_dtype=torch.float16,
        trust_remote_code=True,
    )

    print("Base model loaded.")

    print()
    print("Loading smoke adapter...")

    model = PeftModel.from_pretrained(
        base_model,
        str(ADAPTER_DIR),
    )

    model.eval()

    print("Adapter loaded.")

    device = next(
        model.parameters()
    ).device

    print(
        "Inference device:",
        device
    )

    results = []

    correct = 0
    total = 0

    per_language = {}
    confusion = {}

    print()
    print("=" * 72)
    print("RUNNING ROUTER TEST")
    print("=" * 72)

    for i, row in enumerate(rows, start=1):

        inputs = tokenizer(
            row["prompt"],
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        )

        inputs = {
            k: v.to(device)
            for k, v in inputs.items()
        }

        with torch.no_grad():

            output_ids = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )

        generated_ids = output_ids[
            0
        ][
            inputs["input_ids"].shape[1]:
        ]

        generated = tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        ).strip()

        predicted = extract_predicted(
            generated
        )

        expected = row["expected"]
        language = row["language"]

        is_correct = (
            predicted == expected
        )

        if is_correct:
            correct += 1

        total += 1

        lang = per_language.setdefault(
            language,
            {
                "correct": 0,
                "total": 0,
            }
        )

        lang["total"] += 1

        if is_correct:
            lang["correct"] += 1

        if expected not in confusion:
            confusion[expected] = {}

        pred_key = (
            predicted
            if predicted
            else "NO_INTENT"
        )

        confusion[expected][pred_key] = (
            confusion[expected].get(
                pred_key,
                0
            ) + 1
        )

        results.append({
            "index": i,
            "language": language,
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct,
            "generated": generated,
        })

        if (
            i <= 20
            or not is_correct
        ):

            print()
            print(
                f"[{i}/{len(rows)}]"
            )

            print(
                "LANGUAGE:",
                language
            )

            print(
                "EXPECTED:",
                expected
            )

            print(
                "PREDICTED:",
                predicted
            )

            print(
                "CORRECT:",
                is_correct
            )

            print(
                "OUTPUT:",
                generated[:500]
            )

    accuracy = (
        correct / total * 100
        if total
        else 0.0
    )

    language_summary = {}

    for language, stats in (
        per_language.items()
    ):

        language_summary[language] = {
            "correct":
                stats["correct"],
            "total":
                stats["total"],
            "accuracy_percent":
                (
                    stats["correct"]
                    / stats["total"]
                    * 100
                )
                if stats["total"]
                else 0.0,
        }

    output = {
        "model":
            MODEL_NAME,
        "adapter":
            str(ADAPTER_DIR),
        "test_records":
            total,
        "correct":
            correct,
        "accuracy_percent":
            accuracy,
        "per_language":
            language_summary,
        "confusion":
            confusion,
        "results":
            results,
    }

    RESULT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    RESULT_FILE.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 72)
    print("ROUTER BENCHMARK COMPLETE")
    print("=" * 72)

    print()
    print(
        f"ACCURACY: {correct}/{total} = "
        f"{accuracy:.2f}%"
    )

    print()
    print("BY LANGUAGE:")

    for language, stats in sorted(
        language_summary.items()
    ):

        print(
            f"  {language}: "
            f"{stats['correct']}/"
            f"{stats['total']} = "
            f"{stats['accuracy_percent']:.2f}%"
        )

    print()
    print(
        "[OK] Results:",
        RESULT_FILE
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
