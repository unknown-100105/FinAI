import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parent.parent
TRACE_DIR = ROOT / "xai" / "traces"
SCHEMA_FILE = ROOT / "docs" / "xai_trace_schema.json"


def legacy_errors(data, validation_errors):
    known_legacy = []

    if "claims" not in data:
        known_legacy.append("missing claims")

    policy = data.get("policy", {})

    for field in (
        "authentication_required",
        "confirmation_required",
    ):
        value = policy.get(field)

        if not isinstance(value, bool):
            known_legacy.append(
                f"policy.{field} is not boolean"
            )

    relevant = []

    for error in validation_errors:
        path = list(error.path)

        if (
            error.validator == "required"
            and not path
            and "'claims' is a required property" in error.message
        ):
            relevant.append("missing claims")
            continue

        if (
            error.validator == "type"
            and path == ["policy", "authentication_required"]
            and "boolean" in error.message
        ):
            relevant.append(
                "policy.authentication_required is not boolean"
            )
            continue

        if (
            error.validator == "type"
            and path == ["policy", "confirmation_required"]
            and "boolean" in error.message
        ):
            relevant.append(
                "policy.confirmation_required is not boolean"
            )
            continue

    return (
        bool(known_legacy)
        and set(relevant)
        == set(
            known_legacy
            if all(
                item in known_legacy
                for item in relevant
            )
            else relevant
        )
        and len(relevant) == len(validation_errors)
    )


def main():
    schema = json.loads(
        SCHEMA_FILE.read_text(encoding="utf-8-sig")
    )

    validator = Draft202012Validator(schema)

    trace_files = sorted(TRACE_DIR.glob("*.json"))

    passed = 0
    legacy = 0
    invalid = 0

    print("=" * 80)
    print("FINAI XAI TRACE SCHEMA VALIDATION")
    print("=" * 80)
    print("SCHEMA:", SCHEMA_FILE)
    print("TRACE FILES:", len(trace_files))
    print()

    for path in trace_files:
        try:
            data = json.loads(
                path.read_text(encoding="utf-8-sig")
            )

            errors = sorted(
                validator.iter_errors(data),
                key=lambda error: list(error.path),
            )

            if not errors:
                passed += 1
                print("PASS:", path.name)
                continue

            if legacy_errors(data, errors):
                legacy += 1
                print("LEGACY:", path.name)

                for error in errors:
                    location = ".".join(
                        str(part) for part in error.path
                    )

                    print(
                        "  ",
                        location or "<root>",
                        "->",
                        error.message,
                    )

                continue

            invalid += 1
            print("INVALID:", path.name)

            for error in errors:
                location = ".".join(
                    str(part) for part in error.path
                )

                print(
                    "  ",
                    location or "<root>",
                    "->",
                    error.message,
                )

        except Exception as exc:
            invalid += 1
            print(
                "INVALID:",
                path.name,
                "->",
                repr(exc),
            )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("TOTAL:", len(trace_files))
    print("PASSED:", passed)
    print("LEGACY:", legacy)
    print("INVALID:", invalid)

    if invalid:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
