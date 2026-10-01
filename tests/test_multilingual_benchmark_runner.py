from pathlib import Path

from evaluation.multilingual_benchmark_runner import (
    load_manifest,
    numeric_preservation,
    reference_similarity,
    response_language_match,
    run_benchmark,
)


def test_manifest_loads():

    manifest = load_manifest(
        "evaluation/multilingual_model_benchmark_manifest.json"
    )

    assert manifest["total_cases"] == 100
    assert len(manifest["cases"]) == 100
    assert manifest["languages"]["en"] == 20
    assert manifest["languages"]["ta"] == 20
    assert manifest["languages"]["te"] == 20
    assert manifest["languages"]["kn"] == 20
    assert manifest["languages"]["ml"] == 20


def test_indic_language_detection():

    assert response_language_match(
        "உங்கள் பணம் வெற்றிகரமாக செலுத்தப்பட்டது.",
        "ta",
    )

    assert response_language_match(
        "మీ చెల్లింపు విజయవంతమైంది.",
        "te",
    )

    assert response_language_match(
        "ನಿಮ್ಮ ಪಾವತಿ ಯಶಸ್ವಿಯಾಗಿದೆ.",
        "kn",
    )

    assert response_language_match(
        "നിങ്ങളുടെ പേയ്‌മെന്റ് വിജയിച്ചു.",
        "ml",
    )


def test_english_language_detection():

    assert response_language_match(
        "Your payment was successful.",
        "en",
    )


def test_empty_response_fails():

    assert not response_language_match(
        "",
        "ta",
    )


def test_numeric_preservation():

    reference = (
        "The payment amount is ₹10,000 at 8.5%."
    )

    generated = (
        "தொகை ₹10,000 மற்றும் வட்டி 8.5%."
    )

    assert numeric_preservation(
        reference,
        generated,
    ) is True


def test_missing_numeric_value():

    reference = (
        "EMI is ₹8,678.23 for 20 years."
    )

    generated = (
        "Your EMI is ₹8,000."
    )

    assert numeric_preservation(
        reference,
        generated,
    ) is False


def test_no_numeric_reference():

    assert numeric_preservation(
        "Check your account balance.",
        "உங்கள் கணக்கு இருப்பை சரிபார்க்கவும்.",
    ) is None


def test_reference_similarity():

    score = reference_similarity(
        "Your payment failed.",
        "Your payment failed.",
    )

    assert score > 0.99


def test_benchmark_runner(tmp_path: Path):

    manifest_path = (
        tmp_path / "manifest.json"
    )

    manifest_path.write_text(
        """
        {
          "benchmark": "test",
          "version": "v1",
          "total_cases": 2,
          "languages": {
            "en": 1,
            "ta": 1
          },
          "cases": [
            {
              "case_id": "A",
              "language": "en",
              "intent": "PAYMENT_FAILED",
              "user_text": "My payment failed",
              "reference_response": "Your payment failed."
            },
            {
              "case_id": "B",
              "language": "ta",
              "intent": "PAYMENT_FAILED",
              "user_text": "என் பணம் செலுத்துதல் தோல்வியடைந்தது",
              "reference_response": "உங்கள் பணம் செலுத்துதல் தோல்வியடைந்தது."
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    def fake_generator(
        user_text,
        language,
        intent,
        reference_response,
    ):
        return reference_response

    output = (
        tmp_path / "results.json"
    )

    result = run_benchmark(
        manifest_path,
        model_id="fake-model",
        generator=fake_generator,
        output_path=output,
    )

    assert result["total_cases"] == 2
    assert result["successful_cases"] == 2
    assert result["failed_cases"] == 0
    assert result[
        "response_language_match_rate"
    ] == 1.0

    assert output.exists()
