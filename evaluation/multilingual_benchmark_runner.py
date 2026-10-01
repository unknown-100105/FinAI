from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


LANGUAGE_RANGES = {
    "ta": (0x0B80, 0x0BFF),
    "te": (0x0C00, 0x0C7F),
    "kn": (0x0C80, 0x0CFF),
    "ml": (0x0D00, 0x0D7F),
}

NUMBER_PATTERN = re.compile(
    r"(?:₹|rs\.?|inr)?\s*"
    r"-?\d+(?:,\d{2,3})*(?:\.\d+)?"
    r"(?:\s*%)?",
    re.IGNORECASE,
)


@dataclass
class BenchmarkResult:
    case_id: str
    model_id: str
    language: str
    intent: str
    user_text: str
    reference_response: str
    generated_response: str
    response_non_empty: bool
    response_language_match: bool
    numeric_preservation: Optional[bool]
    reference_similarity: float
    latency_seconds: float
    error: Optional[str] = None


def load_manifest(
    path: str | Path,
) -> Dict:
    path = Path(path)

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    required = {
        "benchmark",
        "version",
        "total_cases",
        "languages",
        "cases",
    }

    missing = required - set(data)

    if missing:
        raise ValueError(
            f"Manifest missing fields: {sorted(missing)}"
        )

    return data


def _has_expected_script(
    text: str,
    language: str,
) -> bool:

    if language == "en":
        return any(
            ch.isascii()
            and ch.isalpha()
            for ch in text
        )

    if language not in LANGUAGE_RANGES:
        return False

    low, high = LANGUAGE_RANGES[language]

    return any(
        low <= ord(ch) <= high
        for ch in text
    )


def response_language_match(
    response: str,
    language: str,
) -> bool:

    response = response.strip()

    if not response:
        return False

    return _has_expected_script(
        response,
        language,
    )


def _numeric_tokens(text: str) -> List[str]:
    tokens = []

    for match in NUMBER_PATTERN.finditer(
        text
    ):
        value = (
            match.group(0)
            .strip()
            .lower()
            .replace(" ", "")
        )

        if value:
            tokens.append(value)

    return tokens


def numeric_preservation(
    reference: str,
    generated: str,
) -> Optional[bool]:

    expected = _numeric_tokens(reference)

    if not expected:
        return None

    actual = _numeric_tokens(generated)

    return all(
        token in actual
        for token in expected
    )


def reference_similarity(
    reference: str,
    generated: str,
) -> float:

    reference = reference.strip()
    generated = generated.strip()

    if not reference or not generated:
        return 0.0

    vectorizer = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 5),
    )

    matrix = vectorizer.fit_transform(
        [reference, generated]
    )

    score = cosine_similarity(
        matrix[0:1],
        matrix[1:2],
    )[0][0]

    return float(score)


def run_benchmark(
    manifest_path: str | Path,
    model_id: str,
    generator: Callable[[str, str, str, str], str],
    output_path: Optional[str | Path] = None,
) -> Dict:

    manifest = load_manifest(
        manifest_path
    )

    cases = manifest["cases"]

    results: List[BenchmarkResult] = []

    for case in cases:

        start = time.perf_counter()

        error = None
        generated = ""

        try:
            generated = generator(
                case["user_text"],
                case["language"],
                case["intent"],
                case["reference_response"],
            )

            if not isinstance(
                generated,
                str,
            ):
                raise TypeError(
                    "Generator must return str."
                )

        except Exception as exc:
            error = (
                f"{type(exc).__name__}: {exc}"
            )

        latency = (
            time.perf_counter()
            - start
        )

        results.append(
            BenchmarkResult(
                case_id=case["case_id"],
                model_id=model_id,
                language=case["language"],
                intent=case["intent"],
                user_text=case["user_text"],
                reference_response=case[
                    "reference_response"
                ],
                generated_response=generated,
                response_non_empty=bool(
                    generated.strip()
                ),
                response_language_match=(
                    response_language_match(
                        generated,
                        case["language"],
                    )
                ),
                numeric_preservation=(
                    numeric_preservation(
                        case["reference_response"],
                        generated,
                    )
                ),
                reference_similarity=round(
                    reference_similarity(
                        case["reference_response"],
                        generated,
                    ),
                    6,
                ),
                latency_seconds=round(
                    latency,
                    6,
                ),
                error=error,
            )
        )

    language_summary = {}

    for language in sorted(
        set(r.language for r in results)
    ):
        subset = [
            r
            for r in results
            if r.language == language
        ]

        language_summary[language] = {
            "cases": len(subset),
            "non_empty_rate": round(
                sum(
                    r.response_non_empty
                    for r in subset
                )
                / len(subset),
                6,
            ),
            "language_match_rate": round(
                sum(
                    r.response_language_match
                    for r in subset
                )
                / len(subset),
                6,
            ),
            "mean_reference_similarity": round(
                sum(
                    r.reference_similarity
                    for r in subset
                )
                / len(subset),
                6,
            ),
        }

    summary = {
        "benchmark": manifest["benchmark"],
        "version": manifest["version"],
        "model_id": model_id,
        "total_cases": len(results),
        "successful_cases": sum(
            r.error is None
            for r in results
        ),
        "failed_cases": sum(
            r.error is not None
            for r in results
        ),
        "response_non_empty_rate": round(
            sum(
                r.response_non_empty
                for r in results
            )
            / len(results),
            6,
        ),
        "response_language_match_rate": round(
            sum(
                r.response_language_match
                for r in results
            )
            / len(results),
            6,
        ),
        "mean_reference_similarity": round(
            sum(
                r.reference_similarity
                for r in results
            )
            / len(results),
            6,
        ),
        "numeric_cases": sum(
            r.numeric_preservation is not None
            for r in results
        ),
        "numeric_preserved": sum(
            r.numeric_preservation is True
            for r in results
        ),
        "mean_latency_seconds": round(
            sum(
                r.latency_seconds
                for r in results
            )
            / len(results),
            6,
        ),
        "per_language": language_summary,
        "results": [
            asdict(r)
            for r in results
        ],
    }

    if output_path is not None:
        output = Path(output_path)

        output.write_text(
            json.dumps(
                summary,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    return summary
