from pathlib import Path
import json
import re
import hashlib
from collections import Counter

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "data" / "source"
WORK = ROOT / "data" / "sft_v3_work"

FINMIX = SOURCE / "finmix" / "train.jsonl"
FINANCE = SOURCE / "finance_instruct" / "train.json"
FINQA = SOURCE / "reasoning" / "finqa" / "data" / "train-00000-of-00001.parquet"
TATQA = SOURCE / "reasoning" / "tatqa" / "tatqa_dataset_train.json"

OUT = WORK / "finai_v3_candidates.jsonl"
MANIFEST = ROOT / "data" / "manifests" / "finai_v3_manifest.json"


def clean(value):
    if value is None:
        return ""

    text = str(value)
    text = text.replace(chr(0), " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def valid_pair(user, answer):
    user = clean(user)
    answer = clean(answer)

    if len(user) < 10:
        return False

    if len(answer) < 1:
        return False

    if len(user) > 20000:
        return False

    if len(answer) > 20000:
        return False

    return True


def add_record(records, seen, source, task, user, answer, metadata=None):
    user = clean(user)
    answer = clean(answer)

    if not valid_pair(user, answer):
        return False

    fingerprint_text = user.lower() + chr(10) + answer.lower()
    key = hashlib.sha256(fingerprint_text.encode("utf-8")).hexdigest()

    if key in seen:
        return False

    seen.add(key)

    row = {
        "source_dataset": source,
        "task_type": task,
        "user": user,
        "assistant": answer,
    }

    if metadata:
        row.update(metadata)

    records.append(row)
    return True


def load_finmix(records, seen):
    accepted = 0

    with FINMIX.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            row = json.loads(line)

            source = clean(row.get("source", ""))

            # FinMix already contains FinQA-derived records.
            if "finqa" in source.lower():
                continue

            if add_record(
                records,
                seen,
                "FinMix",
                clean(row.get("task_type", "financial_instruction")),
                row.get("instruction", ""),
                row.get("output", ""),
                {
                    "source": source,
                    "license": clean(row.get("license", "")),
                    "source_url": clean(row.get("source_url", "")),
                },
            ):
                accepted += 1

    return accepted


def load_finance_instruct(records, seen):
    accepted = 0

    with FINANCE.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            row = json.loads(line)

            if add_record(
                records,
                seen,
                "Finance-Instruct-500k",
                "financial_instruction",
                row.get("user", ""),
                row.get("assistant", ""),
            ):
                accepted += 1

    return accepted


def load_finqa(records, seen):
    accepted = 0

    dataframe = pd.read_parquet(FINQA)

    for _, row in dataframe.iterrows():
        question = clean(row.get("question", ""))
        answer = clean(row.get("answer", ""))
        explanation = clean(row.get("explanation", ""))
        program = clean(row.get("program", ""))

        context_parts = []

        for field in ("pre_text", "post_text"):
            value = row.get(field, "")

            if isinstance(value, (list, tuple)):
                for item in value:
                    item = clean(item)
                    if item:
                        context_parts.append(item)
            else:
                value = clean(value)
                if value:
                    context_parts.append(value)

        table = row.get("table_ori", "")

        if isinstance(table, str):
            table_text = clean(table)
        else:
            table_lines = []

            try:
                for table_row in table:
                    if isinstance(table_row, (list, tuple)):
                        table_lines.append(
                            " | ".join(clean(cell) for cell in table_row)
                        )
            except Exception:
                table_lines = []

            table_text = chr(10).join(table_lines)

        context = chr(10).join(context_parts)

        if table_text:
            if context:
                context += chr(10)
            context += "Table:" + chr(10) + table_text

        if context:
            user_text = (
                "Context:"
                + chr(10)
                + context
                + chr(10)
                + "Question: "
                + question
            )
        else:
            user_text = question

        if explanation:
            answer = answer + " Explanation: " + explanation

        if add_record(
            records,
            seen,
            "FinQA",
            "financial_reasoning",
            user_text,
            answer,
            {
                "reasoning_program": program,
            },
        ):
            accepted += 1

    return accepted


def load_tatqa(records, seen):
    accepted = 0

    with TATQA.open("r", encoding="utf-8") as file:
        documents = json.load(file)

    for document in documents:
        table_object = document.get("table", {})

        if isinstance(table_object, dict):
            table_rows = table_object.get("table", [])
        else:
            table_rows = []

        table_lines = []

        for table_row in table_rows:
            if isinstance(table_row, (list, tuple)):
                table_lines.append(
                    " | ".join(clean(cell) for cell in table_row)
                )

        table_text = chr(10).join(table_lines)

        paragraph_lines = []

        for paragraph in document.get("paragraphs", []):
            if isinstance(paragraph, dict):
                text = clean(paragraph.get("text", ""))
                if text:
                    paragraph_lines.append(text)

        paragraph_text = chr(10).join(paragraph_lines)

        context_parts = []

        if paragraph_text:
            context_parts.append(paragraph_text)

        if table_text:
            context_parts.append("Table:" + chr(10) + table_text)

        context = chr(10).join(context_parts)

        for question in document.get("questions", []):
            if not isinstance(question, dict):
                continue

            question_text = clean(question.get("question", ""))
            answer = question.get("answer", "")

            if isinstance(answer, list):
                answer = ", ".join(clean(x) for x in answer)

            answer = clean(answer)

            if context:
                user_text = (
                    "Context:"
                    + chr(10)
                    + context
                    + chr(10)
                    + "Question: "
                    + question_text
                )
            else:
                user_text = question_text

            if add_record(
                records,
                seen,
                "TAT-QA",
                "financial_table_reasoning",
                user_text,
                answer,
                {
                    "answer_type": clean(question.get("answer_type", "")),
                    "derivation": clean(question.get("derivation", "")),
                },
            ):
                accepted += 1

    return accepted


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(record, ensure_ascii=False)
                + chr(10)
            )


def main():
    WORK.mkdir(parents=True, exist_ok=True)

    records = []
    seen = set()

    print("=" * 72)
    print("FINAI-V3 DATASET BUILDER")
    print("=" * 72)

    finmix_count = load_finmix(records, seen)
    print("FinMix:", finmix_count)

    finance_count = load_finance_instruct(records, seen)
    print("Finance-Instruct-500k:", finance_count)

    finqa_count = load_finqa(records, seen)
    print("FinQA:", finqa_count)

    tatqa_count = load_tatqa(records, seen)
    print("TAT-QA:", tatqa_count)

    by_source = Counter(
        record["source_dataset"]
        for record in records
    )

    by_task = Counter(
        record["task_type"]
        for record in records
    )

    print()
    print("TOTAL UNIQUE CANDIDATES:", len(records))

    print()
    print("BY SOURCE:")
    for name, count in by_source.items():
        print(" ", name, ":", count)

    print()
    print("BY TASK:")
    for name, count in by_task.items():
        print(" ", name, ":", count)

    write_jsonl(OUT, records)

    manifest = {
        "dataset": "FinAI-V3 candidate corpus",
        "records": len(records),
        "records_by_source": dict(by_source),
        "records_by_task": dict(by_task),
        "finmix_finqa_policy": (
            "FinMix records whose source mentions FinQA were excluded."
        ),
        "deduplication": (
            "Exact SHA-256 fingerprint of normalized user+assistant text."
        ),
        "output": str(OUT),
    }

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)

    MANIFEST.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("[OK] Candidate dataset:", OUT)
    print("[OK] Manifest:", MANIFEST)
    print("=" * 72)
    print("FINAI-V3 DATASET BUILD COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
