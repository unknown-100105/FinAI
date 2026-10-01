import json
import re
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, f1_score


MODEL_PATH = Path("router/models/finai_router_tfidf.joblib")
EVAL_PATH = Path("data/sft_v3_work/finai_v3_router_eval_v3.jsonl")


def extract_intent(record):
    for key in ("intent", "label", "target_intent"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for key in ("completion", "output", "assistant", "response", "answer"):
        value = record.get(key)
        if isinstance(value, str):
            match = re.search(r"\bINTENT\s*:\s*([A-Z0-9_]+)", value)
            if match:
                return match.group(1).strip()

    return None


def extract_text(record):
    for key in ("user", "input", "question"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    prompt = record.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        return re.sub(r"^\s*USER\s*:\s*", "", prompt.strip(), flags=re.I)

    return None


rows = []

with open(EVAL_PATH, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue

        record = json.loads(line)

        text = extract_text(record)
        intent = extract_intent(record)

        if text and intent:
            rows.append((text, intent))


model = joblib.load(MODEL_PATH)

texts = [x[0] for x in rows]
y_true = np.array([x[1] for x in rows])

probabilities = model.predict_proba(texts)
classes = np.array(model.named_steps["classifier"].classes_)

top_indices = np.argmax(probabilities, axis=1)
top_predictions = classes[top_indices]
top_confidences = probabilities[np.arange(len(rows)), top_indices]

second_indices = np.argsort(probabilities, axis=1)[:, -2]
second_confidences = probabilities[np.arange(len(rows)), second_indices]

margins = top_confidences - second_confidences

print("=" * 80)
print("FinAI ROUTER CONFIDENCE CALIBRATION")
print("=" * 80)
print(f"Examples: {len(rows)}")
print()

print(
    f"{'THRESHOLD':>10} "
    f"{'ACCEPTED':>10} "
    f"{'COVERAGE':>10} "
    f"{'ACCURACY':>10} "
    f"{'MACRO-F1':>10}"
)
print("-" * 55)

results = []

for threshold in np.arange(0.10, 0.91, 0.05):
    accepted = top_confidences >= threshold

    count = int(accepted.sum())
    coverage = count / len(rows)

    if count:
        accuracy = accuracy_score(
            y_true[accepted],
            top_predictions[accepted]
        )

        macro_f1 = f1_score(
            y_true[accepted],
            top_predictions[accepted],
            average="macro",
            zero_division=0
        )
    else:
        accuracy = 0.0
        macro_f1 = 0.0

    print(
        f"{threshold:10.2f} "
        f"{count:10d} "
        f"{coverage*100:9.2f}% "
        f"{accuracy*100:9.2f}% "
        f"{macro_f1*100:9.2f}%"
    )

    results.append({
        "threshold": float(threshold),
        "accepted": count,
        "coverage": coverage,
        "accuracy": accuracy,
        "macro_f1": macro_f1
    })


print()
print("=" * 80)
print("LOWEST-CONFIDENCE CORRECT PREDICTIONS")
print("=" * 80)

correct = top_predictions == y_true
correct_indices = np.where(correct)[0]

for idx in correct_indices[
    np.argsort(top_confidences[correct_indices])[:15]
]:
    print(
        f"confidence={top_confidences[idx]:.4f} "
        f"actual={y_true[idx]:35s} "
        f"text={texts[idx]}"
    )


print()
print("=" * 80)
print("LOWEST-CONFIDENCE CORRECT PREDICTIONS BY INTENT")
print("=" * 80)

intents = sorted(set(y_true))

for intent in intents:
    indices = np.where((y_true == intent) & correct)[0]

    if len(indices) == 0:
        continue

    idx = indices[np.argmin(top_confidences[indices])]

    print(
        f"{intent:35s} "
        f"{top_confidences[idx]:.4f} "
        f"{texts[idx]}"
    )

output_path = Path("router/evaluation/confidence_calibration.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print()
print(f"Saved: {output_path}")
