import json
import re
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


MODEL_PATH = Path("router/models/finai_router_tfidf.joblib")
EVAL_PATH = Path("data/sft_v3_work/finai_v3_router_eval_v3.jsonl")
RESULT_PATH = Path("router/evaluation/clean_router_results.json")


def extract_intent(record):
    for key in ("intent", "label", "target_intent"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for key in ("completion", "output", "assistant", "response", "answer"):
        value = record.get(key)
        if isinstance(value, str):
            match = re.search(
                r"\bINTENT\s*:\s*([A-Z0-9_]+)",
                value
            )
            if match:
                return match.group(1).strip()

    return None


def extract_user_text(record):
    # Direct user field
    for key in ("user", "question", "input"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Prompt-based schemas
    prompt = record.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        text = prompt.strip()

        # Extract only content after USER:
        matches = re.findall(
            r"USER\s*:\s*(.*?)(?:</FINAI_ROUTER>|$)",
            text,
            flags=re.IGNORECASE | re.DOTALL
        )

        if matches:
            user_text = matches[-1].strip()
        else:
            user_text = text

        # Remove possible wrapper tags
        user_text = re.sub(
            r"</?FINAI_ROUTER>",
            "",
            user_text,
            flags=re.IGNORECASE
        )

        return user_text.strip()

    # Messages schema
    messages = record.get("messages")

    if isinstance(messages, list):
        for message in messages:
            if not isinstance(message, dict):
                continue

            if str(message.get("role", "")).lower() == "user":
                content = message.get("content")

                if isinstance(content, str) and content.strip():
                    return content.strip()

    return None


rows = []

with open(EVAL_PATH, "r", encoding="utf-8") as f:
    for line_number, line in enumerate(f, 1):

        if not line.strip():
            continue

        record = json.loads(line)

        text = extract_user_text(record)
        intent = extract_intent(record)

        if text and intent:
            rows.append({
                "text": text,
                "intent": intent
            })


print("=" * 80)
print("FinAI ROUTER — CLEAN HELD-OUT EVALUATION")
print("=" * 80)

print(f"Evaluation examples: {len(rows)}")
print(f"Unique intents     : {len(set(r['intent'] for r in rows))}")
print()

print("Sample cleaned inputs:")
for row in rows[:10]:
    print(
        f"[{row['intent']}] "
        f"{row['text']}"
    )

print()

model = joblib.load(MODEL_PATH)

texts = [r["text"] for r in rows]
y_true = [r["intent"] for r in rows]

predictions = model.predict(texts)
probabilities = model.predict_proba(texts)

classes = np.array(
    model.named_steps["classifier"].classes_
)

top_indices = np.argmax(probabilities, axis=1)
top_confidence = probabilities[
    np.arange(len(rows)),
    top_indices
]

top_prediction = classes[top_indices]

second_indices = np.argsort(probabilities, axis=1)[:, -2]
second_confidence = probabilities[
    np.arange(len(rows)),
    second_indices
]

margin = top_confidence - second_confidence

accuracy = accuracy_score(y_true, predictions)

report = classification_report(
    y_true,
    predictions,
    zero_division=0,
    output_dict=True
)

print("=" * 80)
print("CLEAN HELD-OUT RESULT")
print("=" * 80)

print(f"Accuracy        : {accuracy:.4f} ({accuracy * 100:.2f}%)")
print(
    f"Macro Precision : "
    f"{report['macro avg']['precision']:.4f}"
)
print(
    f"Macro Recall    : "
    f"{report['macro avg']['recall']:.4f}"
)
print(
    f"Macro F1        : "
    f"{report['macro avg']['f1-score']:.4f}"
)

print()
print("=" * 80)
print("TOP CONFUSIONS")
print("=" * 80)

labels = sorted(set(y_true) | set(predictions))
cm = confusion_matrix(
    y_true,
    predictions,
    labels=labels
)

confusions = []

for i, actual in enumerate(labels):
    for j, predicted in enumerate(labels):
        if i != j and cm[i, j] > 0:
            confusions.append(
                (int(cm[i, j]), actual, predicted)
            )

confusions.sort(reverse=True)

for count, actual, predicted in confusions[:20]:
    print(
        f"{actual:35s} -> "
        f"{predicted:35s} "
        f"{count}"
    )

print()
print("=" * 80)
print("CONFIDENCE THRESHOLD ANALYSIS")
print("=" * 80)

print(
    f"{'THRESHOLD':>10} "
    f"{'ACCEPTED':>10} "
    f"{'COVERAGE':>10} "
    f"{'ACCURACY':>10}"
)

threshold_results = []

for threshold in np.arange(0.10, 0.96, 0.05):

    accepted = top_confidence >= threshold

    accepted_count = int(np.sum(accepted))
    coverage = accepted_count / len(rows)

    if accepted_count:
        accepted_accuracy = accuracy_score(
            np.array(y_true)[accepted],
            top_prediction[accepted]
        )
    else:
        accepted_accuracy = 0.0

    print(
        f"{threshold:10.2f} "
        f"{accepted_count:10d} "
        f"{coverage*100:9.2f}% "
        f"{accepted_accuracy*100:9.2f}%"
    )

    threshold_results.append({
        "threshold": float(threshold),
        "accepted": accepted_count,
        "coverage": coverage,
        "accuracy": accepted_accuracy
    })


print()
print("=" * 80)
print("LOWEST CONFIDENCE CORRECT PREDICTIONS")
print("=" * 80)

correct_mask = (
    np.array(y_true) == top_prediction
)

correct_indices = np.where(correct_mask)[0]

sorted_correct = correct_indices[
    np.argsort(top_confidence[correct_indices])
]

for idx in sorted_correct[:20]:
    print(
        f"{top_confidence[idx]:.4f} | "
        f"{y_true[idx]:30s} | "
        f"{texts[idx]}"
    )


result = {
    "examples": len(rows),
    "intents": len(set(y_true)),
    "accuracy": accuracy,
    "macro_precision": report["macro avg"]["precision"],
    "macro_recall": report["macro avg"]["recall"],
    "macro_f1": report["macro avg"]["f1-score"],
    "thresholds": threshold_results,
    "top_confusions": [
        {
            "actual": a,
            "predicted": p,
            "count": c
        }
        for c, a, p in confusions[:20]
    ]
}

RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(RESULT_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print()
print(f"Results saved to: {RESULT_PATH}")
print()
print("Clean evaluation completed.")
