import json
import random
from pathlib import Path

from transformers import AutoTokenizer


ROOT = Path(__file__).resolve().parent.parent

FINLLM_FILE = (
    ROOT
    / "data"
    / "domain_chunks"
    / "finllm_india_clean_chunks.jsonl"
)

NEWS_FILE = (
    ROOT
    / "data"
    / "domain_chunks"
    / "indian_financial_news_clean_chunks.jsonl"
)

OUTPUT_DIR = ROOT / "data" / "domain_train"

OUTPUT_FILE = OUTPUT_DIR / "domain_train_20k.jsonl"

TOKENIZER_NAME = "sarvamai/sarvam-1"

FINLLM_TARGET = 15000
NEWS_TARGET = 5000

SEED = 42


def load_records(path):
    records = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(
                    json.loads(line)
                )

    return records


def clean_records(records):
    cleaned = []

    seen = set()

    for record in records:

        text = str(
            record.get("text", "")
        ).strip()

        if len(text) < 200:
            continue

        key = text.casefold()

        if key in seen:
            continue

        seen.add(key)

        cleaned.append(record)

    return cleaned


def estimate_tokens(tokenizer, records):

    total_tokens = 0

    batch_size = 32

    texts = [
        record["text"]
        for record in records
    ]

    for start in range(
        0,
        len(texts),
        batch_size
    ):

        batch = texts[
            start:start + batch_size
        ]

        encoded = tokenizer(
            batch,
            add_special_tokens=True,
            truncation=False,
            padding=False,
        )

        total_tokens += sum(
            len(ids)
            for ids in encoded["input_ids"]
        )

        if (
            start + batch_size
        ) % 1000 == 0:

            print(
                "Tokenized:",
                min(
                    start + batch_size,
                    len(texts)
                ),
                "/",
                len(texts)
            )

    return total_tokens


def main():

    random.seed(SEED)

    print("=" * 80)
    print("FINAI DOMAIN TRAINING CORPUS")
    print("=" * 80)

    print("\nLoading FinLLM chunks...")

    finllm = load_records(
        FINLLM_FILE
    )

    print(
        "FinLLM chunks loaded:",
        len(finllm)
    )

    print("\nLoading news chunks...")

    news = load_records(
        NEWS_FILE
    )

    print(
        "News chunks loaded:",
        len(news)
    )

    print("\nCleaning duplicate chunks...")

    finllm = clean_records(finllm)
    news = clean_records(news)

    print(
        "FinLLM after cleaning:",
        len(finllm)
    )

    print(
        "News after cleaning:",
        len(news)
    )

    if len(finllm) < FINLLM_TARGET:
        raise ValueError(
            f"Not enough FinLLM records. "
            f"Need {FINLLM_TARGET}, "
            f"have {len(finllm)}."
        )

    if len(news) < NEWS_TARGET:
        raise ValueError(
            f"Not enough news records. "
            f"Need {NEWS_TARGET}, "
            f"have {len(news)}."
        )

    print("\nSelecting training corpus...")

    random.shuffle(finllm)
    random.shuffle(news)

    selected_finllm = finllm[
        :FINLLM_TARGET
    ]

    selected_news = news[
        :NEWS_TARGET
    ]

    # Add explicit training-source metadata.
    for record in selected_finllm:
        record["training_stage"] = (
            "domain_adaptation"
        )

    for record in selected_news:
        record["training_stage"] = (
            "domain_adaptation"
        )

    combined = (
        selected_finllm
        + selected_news
    )

    random.shuffle(combined)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\nLoading tokenizer for token count...")

    tokenizer = AutoTokenizer.from_pretrained(
        TOKENIZER_NAME
    )

    print("\nEstimating actual token count...")

    total_tokens = estimate_tokens(
        tokenizer,
        combined
    )

    print("\nSaving corpus...")

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:

        for record in combined:

            f.write(
                json.dumps(
                    record,
                    ensure_ascii=False
                )
                + "\n"
            )

    print("\n" + "=" * 80)
    print("DOMAIN TRAINING CORPUS CREATED")
    print("=" * 80)

    print(
        "FinLLM selected :",
        len(selected_finllm)
    )

    print(
        "News selected   :",
        len(selected_news)
    )

    print(
        "Total examples  :",
        len(combined)
    )

    print(
        "Estimated tokens:",
        f"{total_tokens:,}"
    )

    print(
        "Output:",
        OUTPUT_FILE
    )

    print("=" * 80)


if __name__ == "__main__":
    main()