import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

RESULTS = ROOT / "evaluation" / "unseen_results.json"


def extract_intent(output):
    match = re.search(
        r"INTENT:\s*([A-Z0-9_]+)",
        output
    )

    if match:
        return match.group(1).strip()

    return None


def main():
    with RESULTS.open(
        "r",
        encoding="utf-8"
    ) as f:
        results = json.load(f)

    total = len(results)
    correct = 0

    by_language = defaultdict(
        lambda: {"total": 0, "correct": 0}
    )

    print("=" * 70)
    print("FINAI UNSEEN TEST SCORE")
    print("=" * 70)

    for result in results:

        expected = result["expected_intent"]

        predicted = extract_intent(
            result["model_output"]
        )

        language = result["language"]

        by_language[language]["total"] += 1

        if predicted == expected:
            correct += 1
            by_language[language]["correct"] += 1

        print(
            f"{language:3} | "
            f"Expected: {expected:28} | "
            f"Predicted: {predicted}"
        )

    accuracy = (
        correct / total * 100
        if total else 0
    )

    print("\n" + "=" * 70)
    print(f"Overall accuracy: {correct}/{total} = {accuracy:.1f}%")
    print("=" * 70)

    print("\nBy language:")

    for language in sorted(by_language):

        data = by_language[language]

        language_accuracy = (
            data["correct"] /
            data["total"] *
            100
        )

        print(
            f"{language}: "
            f"{data['correct']}/{data['total']} "
            f"({language_accuracy:.1f}%)"
        )

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()