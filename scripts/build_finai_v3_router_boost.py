from pathlib import Path
import json
import hashlib
import random
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]

SEED_FILE = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "training_ready_v2"
    / "train.jsonl"
)

OUTPUT = (
    ROOT
    / "data"
    / "sft_v3_work"
    / "finai_v3_router_boost.jsonl"
)

MANIFEST = (
    ROOT
    / "data"
    / "manifests"
    / "finai_v3_router_boost_manifest.json"
)

RANDOM_SEED = 20260929


# ------------------------------------------------------------------
# Carefully targeted confusion pairs.
# ------------------------------------------------------------------

PAIR_TEMPLATES = {

    ("CARD_LOST", "CARD_STOLEN"): [
        (
            "I can't find my card.",
            "CARD_LOST"
        ),
        (
            "I misplaced my card.",
            "CARD_LOST"
        ),
        (
            "My card is missing.",
            "CARD_LOST"
        ),
        (
            "I don't know where my card is.",
            "CARD_LOST"
        ),
        (
            "My card disappeared from my wallet.",
            "CARD_LOST"
        ),
        (
            "Someone stole my card.",
            "CARD_STOLEN"
        ),
        (
            "My card was stolen.",
            "CARD_STOLEN"
        ),
        (
            "Someone took my card.",
            "CARD_STOLEN"
        ),
        (
            "My card was taken from my bag.",
            "CARD_STOLEN"
        ),
        (
            "My card has been stolen.",
            "CARD_STOLEN"
        ),
    ],

    ("PAYMENT_FAILED", "PAYMENT_PENDING"): [
        (
            "My payment failed.",
            "PAYMENT_FAILED"
        ),
        (
            "The payment was declined.",
            "PAYMENT_FAILED"
        ),
        (
            "My transaction was rejected.",
            "PAYMENT_FAILED"
        ),
        (
            "Why did my payment fail?",
            "PAYMENT_FAILED"
        ),
        (
            "The merchant payment did not go through.",
            "PAYMENT_FAILED"
        ),
        (
            "My payment is still pending.",
            "PAYMENT_PENDING"
        ),
        (
            "The payment has not completed yet.",
            "PAYMENT_PENDING"
        ),
        (
            "Why is my payment pending?",
            "PAYMENT_PENDING"
        ),
        (
            "The transaction is still processing.",
            "PAYMENT_PENDING"
        ),
        (
            "My payment hasn't finished yet.",
            "PAYMENT_PENDING"
        ),
    ],

    ("REFUND_PENDING", "REFUND_RECEIVED"): [
        (
            "My refund is still pending.",
            "REFUND_PENDING"
        ),
        (
            "I have not received my refund yet.",
            "REFUND_PENDING"
        ),
        (
            "When will my refund arrive?",
            "REFUND_PENDING"
        ),
        (
            "The refund has not been credited.",
            "REFUND_PENDING"
        ),
        (
            "My refund is still processing.",
            "REFUND_PENDING"
        ),
        (
            "I received my refund.",
            "REFUND_RECEIVED"
        ),
        (
            "The refund has been credited.",
            "REFUND_RECEIVED"
        ),
        (
            "My refund arrived.",
            "REFUND_RECEIVED"
        ),
        (
            "The refund was deposited into my account.",
            "REFUND_RECEIVED"
        ),
        (
            "I got the refund successfully.",
            "REFUND_RECEIVED"
        ),
    ],

    ("BANK_TRANSFER_FAILED", "BANK_TRANSFER_PENDING"): [
        (
            "My bank transfer failed.",
            "BANK_TRANSFER_FAILED"
        ),
        (
            "The transfer was rejected.",
            "BANK_TRANSFER_FAILED"
        ),
        (
            "Why did my bank transfer fail?",
            "BANK_TRANSFER_FAILED"
        ),
        (
            "My transfer did not go through.",
            "BANK_TRANSFER_FAILED"
        ),
        (
            "The bank transfer was unsuccessful.",
            "BANK_TRANSFER_FAILED"
        ),
        (
            "My bank transfer is still pending.",
            "BANK_TRANSFER_PENDING"
        ),
        (
            "The transfer is still processing.",
            "BANK_TRANSFER_PENDING"
        ),
        (
            "Why is my bank transfer pending?",
            "BANK_TRANSFER_PENDING"
        ),
        (
            "The transfer has not completed yet.",
            "BANK_TRANSFER_PENDING"
        ),
        (
            "My bank transfer hasn't finished.",
            "BANK_TRANSFER_PENDING"
        ),
    ],

    ("WRONG_AMOUNT", "DUPLICATE_TRANSACTION"): [
        (
            "I was charged the wrong amount.",
            "WRONG_AMOUNT"
        ),
        (
            "The transaction amount is incorrect.",
            "WRONG_AMOUNT"
        ),
        (
            "I was charged more than expected.",
            "WRONG_AMOUNT"
        ),
        (
            "The amount deducted is wrong.",
            "WRONG_AMOUNT"
        ),
        (
            "The merchant charged the wrong amount.",
            "WRONG_AMOUNT"
        ),
        (
            "I was charged twice for the same transaction.",
            "DUPLICATE_TRANSACTION"
        ),
        (
            "The same payment appears twice.",
            "DUPLICATE_TRANSACTION"
        ),
        (
            "I see a duplicate transaction.",
            "DUPLICATE_TRANSACTION"
        ),
        (
            "The payment was processed twice.",
            "DUPLICATE_TRANSACTION"
        ),
        (
            "Why is the same transaction listed two times?",
            "DUPLICATE_TRANSACTION"
        ),
    ],

    ("UNKNOWN_TRANSACTION", "FRAUD_REPORT"): [
        (
            "I don't recognize this transaction.",
            "UNKNOWN_TRANSACTION"
        ),
        (
            "What is this transaction on my account?",
            "UNKNOWN_TRANSACTION"
        ),
        (
            "I do not know this payment.",
            "UNKNOWN_TRANSACTION"
        ),
        (
            "There is a transaction I don't recognize.",
            "UNKNOWN_TRANSACTION"
        ),
        (
            "Can you identify this transaction?",
            "UNKNOWN_TRANSACTION"
        ),
        (
            "I think someone used my account fraudulently.",
            "FRAUD_REPORT"
        ),
        (
            "I want to report fraudulent activity.",
            "FRAUD_REPORT"
        ),
        (
            "Someone may have used my account without permission.",
            "FRAUD_REPORT"
        ),
        (
            "I need to report fraud.",
            "FRAUD_REPORT"
        ),
        (
            "There was unauthorized activity on my account.",
            "FRAUD_REPORT"
        ),
    ],

    ("CASH_WITHDRAWAL_FAILED", "CASH_WITHDRAWAL_STATUS"): [
        (
            "My ATM withdrawal failed.",
            "CASH_WITHDRAWAL_FAILED"
        ),
        (
            "The cash withdrawal was declined.",
            "CASH_WITHDRAWAL_FAILED"
        ),
        (
            "I could not withdraw cash.",
            "CASH_WITHDRAWAL_FAILED"
        ),
        (
            "Why did my ATM withdrawal fail?",
            "CASH_WITHDRAWAL_FAILED"
        ),
        (
            "The ATM rejected my withdrawal.",
            "CASH_WITHDRAWAL_FAILED"
        ),
        (
            "What is the status of my cash withdrawal?",
            "CASH_WITHDRAWAL_STATUS"
        ),
        (
            "Can you check my ATM withdrawal status?",
            "CASH_WITHDRAWAL_STATUS"
        ),
        (
            "Is my cash withdrawal still processing?",
            "CASH_WITHDRAWAL_STATUS"
        ),
        (
            "I want to know the status of my withdrawal.",
            "CASH_WITHDRAWAL_STATUS"
        ),
        (
            "Please check the withdrawal status.",
            "CASH_WITHDRAWAL_STATUS"
        ),
    ],
}


def structured_completion(intent):

    tool_map = {
        "CARD_LOST": "block_card",
        "CARD_STOLEN": "block_card",

        "PAYMENT_FAILED": "get_transaction_status",
        "PAYMENT_PENDING": "get_transaction_status",

        "REFUND_PENDING": "get_refund_status",
        "REFUND_RECEIVED": "get_refund_status",

        "BANK_TRANSFER_FAILED":
            "get_bank_transfer_status",

        "BANK_TRANSFER_PENDING":
            "get_bank_transfer_status",

        "WRONG_AMOUNT":
            "get_transaction_status",

        "DUPLICATE_TRANSACTION":
            "get_transaction_status",

        "UNKNOWN_TRANSACTION":
            "get_transaction_status",

        "FRAUD_REPORT":
            "report_fraud",

        "CASH_WITHDRAWAL_FAILED":
            "get_cash_withdrawal_status",

        "CASH_WITHDRAWAL_STATUS":
            "get_cash_withdrawal_status",
    }

    high_risk = {
        "CARD_LOST",
        "CARD_STOLEN",
        "FRAUD_REPORT",
    }

    risk = (
        "high"
        if intent in high_risk
        else "medium"
    )

    tool = tool_map.get(
        intent,
        "NONE"
    )

    return (
        f"INTENT: {intent}\n"
        f"RISK_LEVEL: {risk}\n"
        f"REQUIRES_TOOL: true\n"
        f"TOOL: {tool}\n"
        f"RESPONSE: I can help with this "
        f"financial-service request after the "
        f"required verification and authorization."
    )


def make_router_prompt(user):

    return (
        "<FINAI_ROUTER>\n\n"
        "You are FinAI, a financial-domain assistant.\n\n"
        "Classify the user's financial-service request "
        "and return exactly this format:\n"
        "INTENT: <intent>\n"
        "RISK_LEVEL: <low|medium|high>\n"
        "REQUIRES_TOOL: <true|false>\n"
        "TOOL: <tool name or NONE>\n"
        "RESPONSE: <helpful answer>\n\n"
        "Do not add extra fields.\n\n"
        "USER:\n"
        + user
        + "\n\n"
        "</FINAI_ROUTER>"
    )


def make_key(row):

    text = (
        row["intent"]
        + "\n"
        + row["language"]
        + "\n"
        + row["user"]
    )

    return hashlib.sha256(
        text.lower().encode("utf-8")
    ).hexdigest()


def main():

    print("=" * 72)
    print("FINAI-V3 ROUTER BOOST DATASET")
    print("=" * 72)

    if not SEED_FILE.exists():
        raise FileNotFoundError(SEED_FILE)

    rng = random.Random(
        RANDOM_SEED
    )

    records = []
    seen = set()

    # --------------------------------------------------------------
    # 1. Reuse existing FinAI router records.
    # --------------------------------------------------------------

    with SEED_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line in f:

            if not line.strip():
                continue

            row = json.loads(line)

            if row.get(
                "source_dataset"
            ) not in {
                "FinAI-Intent-Seed",
                "FinAI-Contrastive-Synthetic",
            }:
                continue

            intent = str(
                row.get(
                    "intent",
                    ""
                )
            ).strip()

            user = str(
                row.get(
                    "user",
                    ""
                )
            ).strip()

            language = str(
                row.get(
                    "language",
                    "en"
                )
            ).strip()

            if not intent or not user:
                continue

            record = {
                "source_dataset":
                    row.get(
                        "source_dataset"
                    ),
                "task_type":
                    "finai_router_boost",
                "intent":
                    intent,
                "language":
                    language,
                "user":
                    user,
                "assistant":
                    structured_completion(
                        intent
                    ),
            }

            key = make_key(record)

            if key in seen:
                continue

            seen.add(key)
            records.append(record)

    existing_count = len(
        records
    )

    # --------------------------------------------------------------
    # 2. Add targeted hard negatives.
    # --------------------------------------------------------------

    for pair, templates in (
        PAIR_TEMPLATES.items()
    ):

        for user, intent in templates:

            language = "en"

            record = {
                "source_dataset":
                    "FinAI-Hard-Negative",
                "task_type":
                    "finai_router_boost",
                "intent":
                    intent,
                "language":
                    language,
                "user":
                    user,
                "assistant":
                    structured_completion(
                        intent
                    ),
            }

            key = make_key(record)

            if key in seen:
                continue

            seen.add(key)
            records.append(record)

    # --------------------------------------------------------------
    # 3. Shuffle.
    # --------------------------------------------------------------

    rng.shuffle(records)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT.open(
        "w",
        encoding="utf-8"
    ) as f:

        for row in records:

            row_out = {
                "prompt":
                    make_router_prompt(
                        row["user"]
                    ),
                "completion":
                    row["assistant"],
                "source_dataset":
                    row["source_dataset"],
                "task_type":
                    row["task_type"],
                "intent":
                    row["intent"],
                "language":
                    row["language"],
            }

            f.write(
                json.dumps(
                    row_out,
                    ensure_ascii=False
                ) + "\n"
            )

    by_intent = Counter(
        row["intent"]
        for row in records
    )

    by_source = Counter(
        row["source_dataset"]
        for row in records
    )

    by_language = Counter(
        row["language"]
        for row in records
    )

    manifest = {
        "dataset":
            "FinAI-V3 Router Boost",
        "records":
            len(records),
        "existing_router_records":
            existing_count,
        "hard_negative_records":
            len(records) - existing_count,
        "sources":
            dict(by_source),
        "intents":
            dict(by_intent),
        "languages":
            dict(by_language),
        "note":
            "Targeted router/confusion dataset. "
            "English hard-negative examples are "
            "synthetically authored and should be "
            "validated before final publication.",
        "output":
            str(OUTPUT),
    }

    MANIFEST.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    MANIFEST.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print(
        "EXISTING ROUTER RECORDS:",
        existing_count
    )

    print(
        "HARD-NEGATIVE RECORDS:",
        len(records) - existing_count
    )

    print(
        "TOTAL BOOST RECORDS:",
        len(records)
    )

    print()
    print("BY INTENT:")

    for key, value in sorted(
        by_intent.items()
    ):
        print(
            f"  {key}: {value}"
        )

    print()
    print("BY LANGUAGE:")

    for key, value in sorted(
        by_language.items()
    ):
        print(
            f"  {key}: {value}"
        )

    print()
    print("OUTPUT:", OUTPUT)
    print("MANIFEST:", MANIFEST)

    print()
    print("=" * 72)
    print("ROUTER BOOST DATASET COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
