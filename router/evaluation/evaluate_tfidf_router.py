import json
import re
from pathlib import Path

import joblib
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)


MODEL_PATH = Path("router/models/finai_router_tfidf.joblib")
EVAL_PATH = Path("data/sft_v3_work/finai_v3_router_eval_v3.jsonl")
OUTPUT_PATH = Path("router/evaluation/tfidf_router_results.json")


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


def extract_user_text(record):
    for key in ("user", "input", "question"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    prompt = record.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        text = re.sub(r"^\s*USER\s*:\s*", "", prompt.strip(), flags=re.I)
        return text.strip()

    messages = record.get("messages")
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict):
                if str(msg.get("role", "")).lower() == "user":
                    content = msg.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()

    return None


def load_eval(path):
    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            text = extract_user_text(record)
            intent = extract_intent(record)

            if text and intent:
                rows.append({
                    "text": text,
                    "intent": intent
                })

    return rows


print("=" * 70)
print("FinAI TF-IDF Router — HELD-OUT EVALUATION")
print("=" * 70)

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

if not EVAL_PATH.exists():
    raise FileNotFoundError(f"Evaluation file not found: {EVAL_PATH}")

print(f"Model : {MODEL_PATH}")
print(f"Eval  : {EVAL_PATH}")
print()

model = joblib.load(MODEL_PATH)
rows = load_eval(EVAL_PATH)

texts = [r["text"] for r in rows]
y_true = [r["intent"] for r in rows]

print(f"Evaluation examples: {len(rows)}")
print(f"Evaluation intents : {len(set(y_true))}")
print()

y_pred = model.predict(texts)

accuracy = accuracy_score(y_true, y_pred)

print("=" * 70)
print("OVERALL RESULT")
print("=" * 70)
print(f"Accuracy : {accuracy:.4f}")
print(f"Accuracy : {accuracy * 100:.2f}%")
print()

report_dict = classification_report(
    y_true,
    y_pred,
    zero_division=0,
    output_dict=True
)

print(f"Macro Precision : {report_dict['macro avg']['precision']:.4f}")
print(f"Macro Recall    : {report_dict['macro avg']['recall']:.4f}")
print(f"Macro F1        : {report_dict['macro avg']['f1-score']:.4f}")
print()

print("=" * 70)
print("PER-INTENT RESULTS")
print("=" * 70)

print(classification_report(
    y_true,
    y_pred,
    zero_division=0
))

labels = sorted(set(y_true) | set(y_pred))
cm = confusion_matrix(y_true, y_pred, labels=labels)

confusions = []

for i, actual in enumerate(labels):
    for j, predicted in enumerate(labels):
        if i != j and cm[i, j] > 0:
            confusions.append({
                "actual": actual,
                "predicted": predicted,
                "count": int(cm[i, j])
            })

confusions.sort(key=lambda x: x["count"], reverse=True)

print("=" * 70)
print("TOP CONFUSIONS")
print("=" * 70)

if confusions:
    for item in confusions[:20]:
        print(
            f"{item['actual']:35s} -> "
            f"{item['predicted']:35s} "
            f"{item['count']}"
        )
else:
    print("No incorrect predictions.")

results = {
    "model": "TFIDF_WORD_CHAR_LOGISTIC_REGRESSION",
    "model_path": str(MODEL_PATH),
    "eval_path": str(EVAL_PATH),
    "examples": len(rows),
    "num_intents": len(set(y_true)),
    "accuracy": accuracy,
    "macro_precision": report_dict["macro avg"]["precision"],
    "macro_recall": report_dict["macro avg"]["recall"],
    "macro_f1": report_dict["macro avg"]["f1-score"],
    "top_confusions": confusions[:20],
}

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print()
print(f"Results saved to: {OUTPUT_PATH}")
print()
print("Held-out router evaluation completed.")
