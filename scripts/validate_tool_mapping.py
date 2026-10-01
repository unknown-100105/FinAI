import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TAXONOMY_FILE = PROJECT_ROOT / "data" / "intent_taxonomy.json"
TOOLS_FILE = PROJECT_ROOT / "data" / "tool_catalog.json"
MAPPING_FILE = PROJECT_ROOT / "data" / "intent_tool_map.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    taxonomy = load_json(TAXONOMY_FILE)
    tools = load_json(TOOLS_FILE)
    mapping = load_json(MAPPING_FILE)

    taxonomy_intents = {
        item["intent"]: item
        for item in taxonomy
    }

    errors = []

    # Every taxonomy intent must exist in the mapping.
    missing_intents = (
        set(taxonomy_intents) - set(mapping)
    )

    if missing_intents:
        errors.append(
            f"Missing intents in mapping: {sorted(missing_intents)}"
        )

    # Mapping must not contain unknown intents.
    unknown_intents = (
        set(mapping) - set(taxonomy_intents)
    )

    if unknown_intents:
        errors.append(
            f"Unknown intents in mapping: {sorted(unknown_intents)}"
        )

    # Validate tool references.
    for intent, config in mapping.items():

        tool_name = config.get("tool_name")

        if tool_name is not None and tool_name not in tools:
            errors.append(
                f"{intent} references unknown tool: {tool_name}"
            )

    # Check requires_tool consistency.
    for intent, taxonomy_item in taxonomy_intents.items():

        requires_tool = taxonomy_item["requires_tool"]
        tool_name = mapping.get(intent, {}).get("tool_name")

        if requires_tool and tool_name is None:
            errors.append(
                f"{intent} requires a tool but has no tool mapping."
            )

        if not requires_tool and tool_name is not None:
            errors.append(
                f"{intent} does not require a tool but maps to "
                f"{tool_name}."
            )

    print("=" * 60)
    print("FINAI TOOL MAPPING VALIDATION")
    print("=" * 60)

    print(f"Taxonomy intents : {len(taxonomy_intents)}")
    print(f"Mapping intents  : {len(mapping)}")
    print(f"Available tools  : {len(tools)}")

    if errors:
        print("\nVALIDATION FAILED\n")

        for error in errors:
            print(" -", error)

        raise SystemExit(1)

    print("\nAll intents have valid mappings.")
    print("All referenced tools exist.")
    print("requires_tool flags are consistent.")
    print("\nTOOL MAPPING VALIDATION PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()