import argparse
import json
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import joblib


def extract_intent(record):
    """
    Supports several possible FinAI JSONL schemas.
    Priority:
      1. explicit intent fields
      2. INTENT: inside completion/output/answer
    """
    for key in ("intent", "label", "target_intent"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    candidates = []

    for key in ("completion", "output", "assistant", "response", "answer"):
        value = record.get(key)
        if isinstance(value, str):
            candidates.append(value)

    for text in candidates:
        match = re.search(r"\bINTENT\s*:\s*([A-Z0-9_]+)", text)
        if match:
            return match.group(1).strip()

    return None


def extract_user_text(record):
    """
    Supports the common FinAI schemas:
      user
      prompt
      input
      question
      messages[]
    """
    for key in ("user", "input", "question"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    prompt = record.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        text = prompt.strip()

        # Remove common instruction prefixes where possible.
        text = re.sub(r"^\s*USER\s*:\s*", "", text, flags=re.I)
        return text.strip()

    messages = record.get("messages")
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict):
                role = str(msg.get("role", "")).lower()
                content = msg.get("content")
                if role == "user" and isinstance(content, str) and content.strip():
                    return content.strip()

    return None


def load_jsonl(path):
    rows = []

    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[WARNING] Invalid JSON at line {line_no}: {e}")
                continue

            text = extract_user_text(record)
            intent = extract_intent(record)

            if text and intent:
                rows.append({
                    "text": text,
                    "intent": intent
                })

    return rows


def find_default_train_file():
    candidates = [
        Path("data/sft_v3_work/finai_v3_router_train_v3.jsonl"),
        Path("data/sft_v3_work/finai_v3_router_train.jsonl"),
        Path("data/sft_v3_work/router_train.jsonl"),
        Path("data/sft_v3_work/finai_v3_router_pool_train.jsonl"),
    ]

    for p in candidates:
        if p.exists():
            return p

    raise FileNotFoundError(
        "Could not find the router training file. "
        "Pass --train PATH explicitly."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=str, default=None)
    parser.add_argument(
        "--model-out",
        type=str,
        default="router/models/finai_router_tfidf.joblib"
    )
    args = parser.parse_args()

    train_path = Path(args.train) if args.train else find_default_train_file()

    print("=" * 70)
    print("FinAI Dedicated CPU Router - Training")
    print("=" * 70)
    print(f"Training file: {train_path}")

    rows = load_jsonl(train_path)

    if not rows:
        raise RuntimeError(
            "No usable router examples were found. "
            "Check the JSONL schema/path."
        )

    texts = [r["text"] for r in rows]
    labels = [r["intent"] for r in rows]

    print(f"Usable examples : {len(rows)}")
    print(f"Unique intents   : {len(set(labels))}")
    print()

    counts = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1

    print("Intent distribution:")
    for intent in sorted(counts):
        print(f"  {intent:35s} {counts[intent]}")

    print()
    print("Building multilingual TF-IDF features...")

    # Word features capture intent phrases.
    word_features = TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        min_df=1,
        sublinear_tf=True,
        max_features=120000
    )

    # Character features help with:
    # - Indian language scripts
    # - spelling mistakes
    # - code-mixing
    # - short banking phrases
    char_features = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=1,
        sublinear_tf=True,
        max_features=160000
    )

    features = FeatureUnion([
        ("word", word_features),
        ("char", char_features),
    ])

    classifier = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        solver="saga",
        n_jobs=-1
    )

    pipeline = Pipeline([
        ("features", features),
        ("classifier", classifier),
    ])

    print("Training CPU router...")
    pipeline.fit(texts, labels)

    predictions = pipeline.predict(texts)
    accuracy = accuracy_score(labels, predictions)

    print()
    print("=" * 70)
    print("TRAINING SET RESULT")
    print("=" * 70)
    print(f"Training accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")
    print()

    print("Per-intent training report:")
    print(classification_report(
        labels,
        predictions,
        zero_division=0
    ))

    model_out = Path(args.model_out)
    model_out.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(pipeline, model_out)

    metadata = {
        "model_type": "TFIDF_WORD_CHAR_LOGISTIC_REGRESSION",
        "training_examples": len(rows),
        "num_intents": len(set(labels)),
        "intents": sorted(set(labels)),
        "features": {
            "word_ngram": [1, 2],
            "char_wb_ngram": [2, 5]
        }
    }

    metadata_path = model_out.with_suffix(".json")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Model saved to: {model_out}")
    print(f"Metadata saved to: {metadata_path}")
    print()
    print("Router training completed successfully.")


if __name__ == "__main__":
    main()
