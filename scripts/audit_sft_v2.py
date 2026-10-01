import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DATA_FILE = (
    ROOT
    / "data"
    / "sft_v2"
    / "train.jsonl"
)

TAXONOMY_FILE = (
    ROOT
    / "data"
    / "intent_taxonomy.json"
)

MAPPING_FILE = (
    ROOT
    / "data"
    / "intent_tool_map.json"
)

OUTPUT_FILE = (
    ROOT
    / "evaluation"
    / "sft_v2_audit.json"
)


def load_jsonl(path):

    records = []

    with path.open(
        "r",
        encoding="utf-8"
    ) as f:

        for line_number, line in enumerate(
            f,
            start=1
        ):

            line = line.strip()

            if not line:
                continue

            try:

                record = json.loads(line)

                record["_line"] = line_number

                records.append(record)

            except json.JSONDecodeError:

                print(
                    f"Malformed JSON at line {line_number}"
                )

    return records


def load_json(path):

    with path.open(
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


def main():

    print("=" * 70)
    print("FINAI SFT-v2 DATASET AUDIT")
    print("=" * 70)

    if not DATA_FILE.exists():

        raise FileNotFoundError(
            f"Dataset not found: {DATA_FILE}"
        )

    records = load_jsonl(
        DATA_FILE
    )

    taxonomy = (
        load_json(TAXONOMY_FILE)
        if TAXONOMY_FILE.exists()
        else []
    )

    mapping = (
        load_json(MAPPING_FILE)
        if MAPPING_FILE.exists()
        else {}
    )

    # --------------------------------------------------------
    # Basic counts
    # --------------------------------------------------------

    languages = Counter()
    intents = Counter()
    risks = Counter()
    tools = Counter()

    missing_prompt = 0
    missing_completion = 0
    missing_intent = 0
    missing_language = 0

    duplicate_prompts = 0

    seen_prompts = set()

    malformed_tool_mapping = 0
    tool_required_without_tool = 0
    tool_not_required_with_tool = 0

    # --------------------------------------------------------
    # Analyze records
    # --------------------------------------------------------

    for record in records:

        language = str(
            record.get(
                "language",
                ""
            )
        ).strip().lower()

        intent = str(
            record.get(
                "intent",
                ""
            )
        ).strip().upper()

        risk = str(
            record.get(
                "risk_level",
                ""
            )
        ).strip().lower()

        prompt = str(
            record.get(
                "prompt",
                ""
            )
        ).strip()

        completion = str(
            record.get(
                "completion",
                ""
            )
        ).strip()

        tool_name = str(
            record.get(
                "tool_name",
                ""
            )
        ).strip()

        requires_tool = bool(
            record.get(
                "requires_tool",
                False
            )
        )

        # Counters
        languages[language] += 1
        intents[intent] += 1
        risks[risk] += 1

        if tool_name:
            tools[tool_name] += 1

        # Required fields
        if not prompt:
            missing_prompt += 1

        if not completion:
            missing_completion += 1

        if not intent:
            missing_intent += 1

        if not language:
            missing_language += 1

        # Duplicate prompts
        prompt_key = prompt.casefold()

        if prompt_key in seen_prompts:

            duplicate_prompts += 1

        else:

            seen_prompts.add(
                prompt_key
            )

        # Tool consistency
        expected_tool = mapping.get(
            intent
        )

        if requires_tool and not tool_name:

            tool_required_without_tool += 1

        if not requires_tool and tool_name:

            tool_not_required_with_tool += 1

        if (
            tool_name
            and expected_tool is not None
            and tool_name != expected_tool
        ):

            malformed_tool_mapping += 1

    # --------------------------------------------------------
    # Expected intents
    # --------------------------------------------------------

    taxonomy_intents = set()

    if isinstance(taxonomy, list):

        for item in taxonomy:

            if isinstance(item, dict):

                name = str(
                    item.get(
                        "intent",
                        ""
                    )
                ).strip().upper()

                if name:
                    taxonomy_intents.add(name)

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    missing_taxonomy_intents = (
        sorted(
            taxonomy_intents
            - set(intents.keys())
        )
    )

    unknown_dataset_intents = (
        sorted(
            set(intents.keys())
            - taxonomy_intents
        )
        if taxonomy_intents
        else []
    )

    report = {

        "total_records": len(records),

        "languages": dict(
            languages.most_common()
        ),

        "intents": dict(
            intents.most_common()
        ),

        "risk_levels": dict(
            risks.most_common()
        ),

        "tools": dict(
            tools.most_common()
        ),

        "quality": {

            "missing_prompt":
                missing_prompt,

            "missing_completion":
                missing_completion,

            "missing_intent":
                missing_intent,

            "missing_language":
                missing_language,

            "duplicate_prompts":
                duplicate_prompts,

            "tool_required_without_tool":
                tool_required_without_tool,

            "tool_not_required_with_tool":
                tool_not_required_with_tool,

            "malformed_tool_mapping":
                malformed_tool_mapping,
        },

        "taxonomy": {

            "taxonomy_intent_count":
                len(taxonomy_intents),

            "missing_dataset_intents":
                missing_taxonomy_intents,

            "unknown_dataset_intents":
                unknown_dataset_intents,
        },
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2
        )

    # --------------------------------------------------------
    # Console report
    # --------------------------------------------------------

    print(
        "\nTotal records:",
        len(records)
    )

    print(
        "\nLanguage distribution:"
    )

    for language, count in languages.most_common():

        print(
            f"  {language}: {count}"
        )

    print(
        "\nUnique intents:",
        len(intents)
    )

    print(
        "\nTop intents:"
    )

    for intent, count in intents.most_common(15):

        print(
            f"  {intent}: {count}"
        )

    print(
        "\nRisk distribution:"
    )

    for risk, count in risks.items():

        print(
            f"  {risk}: {count}"
        )

    print(
        "\nQuality checks:"
    )

    print(
        "  Missing prompt:",
        missing_prompt
    )

    print(
        "  Missing completion:",
        missing_completion
    )

    print(
        "  Missing intent:",
        missing_intent
    )

    print(
        "  Missing language:",
        missing_language
    )

    print(
        "  Duplicate prompts:",
        duplicate_prompts
    )

    print(
        "  Tool required without tool:",
        tool_required_without_tool
    )

    print(
        "  Tool not required with tool:",
        tool_not_required_with_tool
    )

    print(
        "  Malformed tool mappings:",
        malformed_tool_mapping
    )

    print(
        "\nAudit saved to:"
    )

    print(OUTPUT_FILE)

    print("\n" + "=" * 70)
    print("SFT-v2 AUDIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()