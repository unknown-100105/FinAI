from rag.evidence_verifier import RAGEvidenceVerifier


def evidence():
    return [
        {
            "document_id": 1,
            "title": "KYC requirements",
            "source": "test",
            "date": "2025-01-01",
            "text": (
                "KYC may require PAN card, address proof, photograph, "
                "cancelled cheque, and signatures."
            ),
        }
    ]


def test_supported_rag_response_passes():
    result = RAGEvidenceVerifier.verify(
        (
            "KYC may require a PAN card and address proof. "
            "A photograph and cancelled cheque may also be required."
        ),
        evidence(),
    )

    assert result["applicable"] is True
    assert result["mode"] == "EVIDENCE_SUPPORT"
    assert result["passed"] is True
    assert result["unsupported_claims"] == []
    assert len(result["supported_claims"]) == 2


def test_unsupported_rag_claim_fails():
    result = RAGEvidenceVerifier.verify(
        (
            "KYC may require a PAN card. "
            "KYC guarantees approval of every loan application."
        ),
        evidence(),
    )

    assert result["applicable"] is True
    assert result["passed"] is False
    assert result["supported_claims"]
    assert len(result["unsupported_claims"]) == 1
    assert "guarantees approval" in result["unsupported_claims"][0]["claim"]


def test_no_rag_evidence_fails_safely():
    result = RAGEvidenceVerifier.verify(
        "KYC requires a PAN card.",
        [],
    )

    assert result["applicable"] is True
    assert result["passed"] is False
    assert result["evidence_count"] == 0
    assert result["unsupported_claims"]


def test_empty_response_is_not_grounded():
    result = RAGEvidenceVerifier.verify(
        "",
        evidence(),
    )

    assert result["applicable"] is True
    assert result["passed"] is False

def test_strong_qualifier_without_matching_evidence_fails():
    result = RAGEvidenceVerifier.verify(
        "All KYC processes always support digital verification.",
        [
            {
                "title": "KYC evidence",
                "text": "Digital KYC is available in some cases.",
            }
        ],
    )

    assert result["passed"] is False
    assert result["unsupported_claims"]
    assert (
        result["unsupported_claims"][0]["qualifier_supported"]
        is False
    )


def test_conflicting_qualifier_and_caveat_fails():
    result = RAGEvidenceVerifier.verify(
        "All KYC processes support digital verification in some cases.",
        [
            {
                "title": "KYC evidence",
                "text": "Digital KYC is available in some cases.",
            }
        ],
    )

    assert result["passed"] is False
    assert result["unsupported_claims"][0]["internal_qualifier_conflict"] is True
