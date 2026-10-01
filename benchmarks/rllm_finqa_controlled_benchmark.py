import json
import time
from pathlib import Path

from llm.rllm_finqa_adapter import RLLMFinQAModelAdapter


CASES = [
    {
        "id": "emi_grounded",
        "intent": "EMI_QUERY",
        "source": "deterministic_finance_engine",
        "language": "English",
        "persona": "neutral",
        "user_text": "Explain this EMI result clearly to me.",
        "verified_result": {
            "principal": 1000000,
            "annual_rate": 8.5,
            "tenure_months": 240,
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        "required_values": ["8678.23", "2082775.76", "1082775.76"],
    },
    {
        "id": "emi_no_recalculation",
        "intent": "EMI_QUERY",
        "source": "deterministic_finance_engine",
        "language": "English",
        "persona": "neutral",
        "user_text": "Explain the supplied EMI result. Do not recalculate or change any numbers.",
        "verified_result": {
            "principal": 500000,
            "annual_rate": 10.0,
            "tenure_months": 60,
            "monthly_emi": 10624.55,
            "total_payment": 637473.00,
            "total_interest": 137473.00,
        },
        "required_values": ["10624.55", "637473.00", "137473.00"],
    },
    {
        "id": "interest_grounded",
        "intent": "INTEREST_QUERY",
        "source": "deterministic_finance_engine",
        "language": "English",
        "persona": "neutral",
        "user_text": "Explain the supplied compound-interest result.",
        "verified_result": {
            "principal": 100000,
            "annual_rate": 8.0,
            "tenure_years": 5,
            "compounding": "monthly",
            "final_amount": 148984.57,
            "interest_earned": 48984.57,
        },
        "required_values": ["148984.57", "48984.57"],
    },
    {
        "id": "numerical_preservation",
        "intent": "EMI_QUERY",
        "source": "deterministic_finance_engine",
        "language": "English",
        "persona": "neutral",
        "user_text": "Summarize the verified result without modifying any financial values.",
        "verified_result": {
            "principal": 2500000,
            "annual_rate": 7.25,
            "tenure_months": 180,
            "monthly_emi": 22826.41,
            "total_payment": 4108753.80,
            "total_interest": 1608753.80,
        },
        "required_values": ["22826.41", "4108753.80", "1608753.80"],
    },
    {
        "id": "missing_value_non_invention",
        "intent": "EMI_QUERY",
        "source": "deterministic_finance_engine",
        "language": "English",
        "persona": "neutral",
        "user_text": "Explain the supplied EMI information. Do not invent any missing financial values.",
        "verified_result": {
            "principal": 800000,
            "annual_rate": 9.0,
            "tenure_months": 120,
            "monthly_emi": 10133.70,
        },
        "required_values": ["10133.70"],
    },
    {
        "id": "persona_facts",
        "intent": "EMI_QUERY",
        "source": "deterministic_finance_engine",
        "language": "English",
        "persona": "financial_hype_man",
        "user_text": "Explain this result in an energetic but financially accurate way.",
        "verified_result": {
            "principal": 1000000,
            "annual_rate": 8.5,
            "tenure_months": 240,
            "monthly_emi": 8678.23,
            "total_payment": 2082775.76,
            "total_interest": 1082775.76,
        },
        "required_values": ["8678.23", "2082775.76", "1082775.76"],
    },
]


def normalize_number(value):
    text = str(value)
    return (
        text.replace(",", "")
        .replace("₹", "")
        .replace("$", "")
        .replace("Rs", "")
        .strip()
    )



def run_case(adapter, case):
    started = time.perf_counter()

    result = adapter.generate(
        user_text=case["user_text"],
        intent=case["intent"],
        verified_result=case["verified_result"],
        source=case["source"],
        language=case["language"],
        persona=case["persona"],
        max_new_tokens=512,
    )

    elapsed = time.perf_counter() - started
    response = result.get("response", "")

    checks = {}
    response_normalized = (
        response
        .replace(",", "")
        .replace("₹", "")
        .replace("$", "")
        .replace("Rs", "")
    )

    import re

    numeric_candidates = re.findall(
        r"(?<![\d.])\d+(?:\.\d+)?",
        response_normalized,
    )

    for value in case["required_values"]:
        expected = float(normalize_number(value))
        found = False

        for candidate in numeric_candidates:
            try:
                if abs(float(candidate) - expected) <= 0.01:
                    found = True
                    break
            except ValueError:
                continue

        checks[value] = found

    semantic_numeric_pass = all(checks.values())

    forbidden_action_phrases = [
        "execute the transfer",
        "block your card",
        "reset your password",
        "approve the transaction",
    ]
    action_violation = any(
        phrase in response.lower()
        for phrase in forbidden_action_phrases
    )

    generated_tokens = result.get("metrics", {}).get(
        "generated_tokens", 0
    )

    max_new_tokens = 512
    truncated_or_incomplete = generated_tokens >= max_new_tokens

    passed = (
        semantic_numeric_pass
        and not action_violation
    )

    return {
        "id": case["id"],
        "intent": case["intent"],
        "status": result.get("status"),
        "passed": passed,
        "required_value_checks": checks,
        "semantic_numeric_pass": semantic_numeric_pass,
        "exact_formatting_pass": all(
            str(value) in response.replace(",", "")
            for value in case["required_values"]
        ),
        "action_violation": action_violation,
        "truncated_or_incomplete": truncated_or_incomplete,
        "elapsed_seconds": round(elapsed, 3),
        "metrics": result.get("metrics", {}),
        "response": response,
    }


def main():
    adapter = RLLMFinQAModelAdapter()

    results = []

    print("=" * 80)
    print("FINAI rLLM-FinQA-4B CONTROLLED BENCHMARK")
    print("=" * 80)

    for index, case in enumerate(CASES, start=1):
        print(f"\n[{index}/{len(CASES)}] {case['id']}")
        result = run_case(adapter, case)
        results.append(result)

        print("PASS:", result["passed"])
        print("TOKENS:", result["metrics"].get("generated_tokens"))
        print("TOKENS/SEC:", round(result["metrics"].get("tokens_per_second", 0), 2))
        print("REQUIRED VALUES:", result["required_value_checks"])
        print("ACTION VIOLATION:", result["action_violation"])
        print("RESPONSE:")
        print(result["response"])

    passed = sum(r["passed"] for r in results)
    total = len(results)

    semantic_passed = sum(
        r["semantic_numeric_pass"]
        and not r["action_violation"]
        for r in results
    )

    complete_responses = sum(
        not r["truncated_or_incomplete"]
        for r in results
    )

    summary = {
        "model": "rllm-finqa-4b",
        "total_cases": total,
        "passed_cases": passed,
        "failed_cases": total - passed,
        "accuracy": round(passed / total, 4),
        "semantic_grounding_score": round(
            semantic_passed / total, 4
        ),
        "completion_rate": round(
            complete_responses / total, 4
        ),
        "results": results,
    }

    output_dir = Path("benchmarks")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "rllm_finqa_controlled_benchmark.json"
    output_file.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY")
    print("=" * 80)
    print("MODEL:", summary["model"])
    print("CASES:", total)
    print("PASSED:", passed)
    print("FAILED:", total - passed)
    print("SCORE:", f"{summary['accuracy'] * 100:.2f}%")
    print(
        "SEMANTIC GROUNDING:",
        f"{summary['semantic_grounding_score'] * 100:.2f}%"
    )
    print(
        "COMPLETION RATE:",
        f"{summary['completion_rate'] * 100:.2f}%"
    )
    print("RESULT FILE:", output_file)


if __name__ == "__main__":
    main()
